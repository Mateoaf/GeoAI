"""Fase E: protocolo espacial anidado y diseños P/U, sin ajustar modelos.

Modo diagnóstico explícito: los candidatos nunca se promocionan a positivos
revisados. Todas las decisiones y máscaras quedan ligadas a una ejecución D.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import importlib.metadata
import json
import shutil

import numpy as np
import pandas as pd
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree
import yaml

from .local_sources import sha256_file, write_json


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def verify(base,entries):
    for entry in entries:
        p=Path(base)/entry['path']
        if not p.is_file() or sha256_file(p)!=entry['sha256']:
            raise ValueError(f'Archivo modificado o ausente: {p}')


def records(base,paths):
    return [{'path':p.relative_to(base).as_posix(),'sha256':sha256_file(p)} for p in paths]


def seed_for(seed,*parts):
    text='|'.join(map(str,(seed,*parts)))
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8],'big')


def atomic_parquet(frame,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name('.'+path.name+'.tmp')
    frame.to_parquet(temporary,index=False)
    temporary.replace(path)


def check_config(cfg,resolution):
    if cfg['mode'] not in ('diagnostic','validated') or cfg['target'] not in ('general','roca','aluvial'):
        raise ValueError('Modo u objetivo inválido.')
    for name in ('block_size_m',):
        if cfg[name]<resolution or cfg[name]%resolution:raise ValueError('Bloques deben ser múltiplos de la resolución.')
    if any(v<resolution or v%resolution for v in cfg['sensitivity_block_sizes_m']):raise ValueError('Tamaños de sensibilidad inválidos.')
    if not 0<cfg['holdout_fraction']<.5:raise ValueError('Reserva debe estar entre 0 y 0,5.')
    for key in ('outer_folds','inner_folds','realizations','minimum_positive_units_test','minimum_positive_units_train'):
        if not isinstance(cfg[key],int) or cfg[key]<1:raise ValueError(key)
    if min(cfg['outer_folds'],cfg['inner_folds'])<2:raise ValueError('Se requieren al menos dos folds.')
    for key in ('spatial_gap_m','background_buffer_m'):
        if not np.isfinite(cfg[key]) or cfg[key]<0:raise ValueError(key)
    if not cfg['ratios_u_to_p'] or any(not isinstance(v,int) or v<=0 for v in cfg['ratios_u_to_p']):raise ValueError('Ratios inválidos.')


def source_data(root,cfg):
    d=Path(root)/cfg['phase_d_run']
    control=read_json(d/'control_cierre.json')
    if control['estado_ejecucion']!='completada':raise ValueError('D no está terminada técnicamente.')
    verify(d,read_json(d/'outputs_manifest.json'))
    grid=pd.read_parquet(d/'calidad_y_soporte.parquet')
    needed=['cell_id','row','col','x_center','y_center','land_area_m2',cfg['support_column']]
    grid=grid[needed].copy().rename(columns={cfg['support_column']:'eligible'}).reset_index(drop=True)
    if not grid.cell_id.is_unique or grid.cell_id.isna().any():raise ValueError('Claves inválidas en D.')
    if grid.eligible.isna().any() or not grid.eligible.isin([True,False]).all():raise ValueError('Soporte debe ser booleano.')
    spec=read_json(d/'grid_spec.json');check_config(cfg,spec['resolution_m'])
    relations=pd.read_parquet(d/'relacion_indicios_celda.parquet')
    if not relations.record_id.is_unique:raise ValueError('Indicios duplicados por record_id.')
    groupmap=None
    if cfg.get('territorial_groups_path'):
        groupmap=pd.read_csv(Path(root)/cfg['territorial_groups_path'],dtype='string')
        if not groupmap.cell_id.is_unique or set(groupmap.cell_id)!=set(grid.cell_id):raise ValueError('Mapa territorial incompleto/duplicado.')
        if 'district_id' not in groupmap:raise ValueError('Falta district_id en mapa territorial.')
    return d,grid,relations,spec,groupmap


def choose_labels(grid,relations,cfg):
    assigned=relations[relations.cell_id.isin(grid.cell_id)].copy()
    if cfg['target']!='general':assigned=assigned[assigned.tipo_au_final==cfg['target']]
    eligible=set(grid.loc[grid.eligible,'cell_id'])
    assigned=assigned[assigned.cell_id.isin(eligible)]
    reviewed_field=f'elegible_{cfg["target"]}_revisada'
    # No se acepta astype(bool) sobre cadenas "False".
    if assigned[reviewed_field].isna().any() or not assigned[reviewed_field].isin([True,False]).all():
        raise ValueError(f'Etiqueta no booleana: {reviewed_field}')
    reviewed=assigned[assigned[reviewed_field]].copy()
    selected=assigned if cfg['mode']=='diagnostic' else reviewed
    return selected,reviewed


def readiness(root,cfg,grid,relations,groupmap):
    selected,reviewed=choose_labels(grid,relations,cfg)
    allow=read_json(Path(root)/cfg['phase_d_run']/'feature_allowlist.json')
    reasons=[]
    if reviewed.empty:reasons.append('No hay positivos revisados con soporte para este objetivo.')
    for col in ('deposit_id','district_id'):
        if reviewed.empty or reviewed[col].fillna('').astype(str).str.strip().eq('').any():
            reasons.append(f'Faltan {col} validados en los positivos.')
    if not allow['approved_training_columns']:reasons.append('D no contiene predictores aprobados para entrenamiento.')
    if groupmap is None:reasons.append('Falta cartografía territorial de distritos: no basta con IDs en los indicios.')
    else:
        mapped=reviewed[['cell_id','district_id']].merge(groupmap[['cell_id','district_id']],on='cell_id',suffixes=('_record','_map'),validate='many_to_one')
        if (mapped.district_id_record.fillna('')!=mapped.district_id_map.fillna('')).any():reasons.append('Distritos de indicios y cartografía discordantes.')
    if cfg['target']=='aluvial' and (groupmap is None or 'catchment_id' not in groupmap or groupmap.catchment_id.isna().any()):
        reasons.append('Faltan cuencas completas para el objetivo aluvial.')
    if not cfg['reserve_district_ids']:reasons.append('Falta selección revisada de distritos para reserva final.')
    if not cfg['protocol_reviewed']:reasons.append('Protocolo espacial pendiente de revisión.')
    return {'ready_for_scientific_training':not reasons,'reasons':reasons,
            'reviewed_positive_cells':int(reviewed.cell_id.nunique()),
            'diagnostic_or_selected_positive_cells':int(selected.cell_id.nunique()),
            'selected_role':'P_candidate_proxy' if cfg['mode']=='diagnostic' else 'P_reviewed'}


def start_run(root):
    root=Path(root).resolve();path=root/'config/evaluation.yaml'
    cfg=yaml.safe_load(path.read_text(encoding='utf-8'))
    d,grid,relations,spec,groupmap=source_data(root,cfg)
    gate=readiness(root,cfg,grid,relations,groupmap)
    if cfg['mode']=='validated' and not gate['ready_for_scientific_training']:
        raise ValueError('Modo validado no disponible: '+'; '.join(gate['reasons']))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    out=root/cfg['output_directory']/stamp;out.mkdir(parents=True,exist_ok=False)
    for sub in ('design','memberships','samples'): (out/sub).mkdir()
    frozen=[path,Path(__file__).resolve(),root/'src/geoau/local_sources.py',d/'outputs_manifest.json']
    if cfg.get('territorial_groups_path'):frozen.append(root/cfg['territorial_groups_path'])
    write_json(out/'inputs.json',{'phase_d_run':cfg['phase_d_run'],'frozen':records(root,frozen)})
    write_json(out/'config_snapshot.json',cfg);write_json(out/'readiness.json',gate)
    write_json(out/'grid_spec.json',spec)
    write_json(out/'environment.json',{n:importlib.metadata.version(n) for n in ('numpy','pandas','scipy','pyarrow','PyYAML')})
    shutil.copy2(Path(__file__),out/'evaluation_source.py')
    atomic_parquet(grid,out/'territory.parquet')
    write_json(out/'control_cierre.json',{'estado_ejecucion':'en_curso','mode':cfg['mode'],'training_allowed':False})
    write_json(out.parent/'current_run.json',{'run':out.relative_to(root).as_posix()})
    print('Fase E:',out,flush=True)
    return out


def current_run(root):
    root=Path(root).resolve();cfg=yaml.safe_load((root/'config/evaluation.yaml').read_text(encoding='utf-8'))
    out=root/read_json(root/cfg['output_directory']/'current_run.json')['run']
    if cfg!=read_json(out/'config_snapshot.json'):raise ValueError('Cambió configuración: iniciar nueva E con 07.')
    verify(root,read_json(out/'inputs.json')['frozen'])
    return out


def ensure_run(root):
    try:return current_run(root)
    except (FileNotFoundError,ValueError):return start_run(root)


def context(root,out):
    root,out=Path(root).resolve(),Path(out).resolve()
    verify(root,read_json(out/'inputs.json')['frozen'])
    cfg=read_json(out/'config_snapshot.json')
    d,grid,relations,spec,groupmap=source_data(root,cfg)
    return cfg,grid,relations,spec,groupmap


def connected_units(grid,relations,block_size,resolution,group_columns,groupmap=None):
    """Unión transitiva de bloques ligados por depósitos/distritos/grupos."""
    blocks=('b'+(grid.row*resolution//block_size).astype(str)+'_'+(grid.col*resolution//block_size).astype(str)).to_numpy()
    parent={b:b for b in sorted(set(blocks))}
    def find(b):
        while parent[b]!=b:
            parent[b]=parent[parent[b]];b=parent[b]
        return b
    def union(items):
        roots=sorted({find(b) for b in items})
        for b in roots[1:]:parent[b]=roots[0]
    mapping=pd.DataFrame({'cell_id':grid.cell_id,'block_id':blocks})
    link=relations[relations.cell_id.notna()].merge(mapping,on='cell_id',validate='many_to_one')
    links=[]
    for col in group_columns:
        values=link[col].fillna('').astype(str).str.strip()
        for value,part in link.loc[values.ne('')].groupby(values[values.ne('')],sort=True):
            union(part.block_id.unique());links.append({'group_type':col,'group_id':value,'blocks':part.block_id.nunique()})
    if groupmap is not None:
        territory=mapping.merge(groupmap,on='cell_id',validate='one_to_one')
        for col in ('district_id','catchment_id'):
            if col not in territory:continue
            for value,part in territory.dropna(subset=[col]).groupby(col,sort=True):
                if str(value).strip():union(part.block_id.unique())
    units=np.array([find(b) for b in blocks])
    return mapping.assign(unit_id=units),pd.DataFrame(links,columns=['group_type','group_id','blocks'])


def assign_fold(units,n_folds,seed,*salt):
    # Reparte unidades completas; no usa X ni scores, ni balancea con y de prueba.
    ordered=sorted(set(units),key=lambda u:(seed_for(seed,*salt,u),u))
    return {u:i%n_folds for i,u in enumerate(ordered)}


def distance_lower_bound(grid,reference,spec):
    """Cota inferior entre huellas cuadradas completas, no solo sus centros."""
    if not np.any(reference):return np.full(len(grid),np.inf)
    mask=np.ones((spec['height'],spec['width']),dtype=bool)
    rr=grid.row.to_numpy();cc=grid.col.to_numpy()
    mask[rr[reference],cc[reference]]=False
    distance=distance_transform_edt(mask,sampling=spec['resolution_m'])[rr,cc]
    return np.maximum(0,distance-np.sqrt(2)*spec['resolution_m'])


def split_membership(grid,units,holdout,parent_train,fold_map,fold,spec,gap,positive_cells):
    assignment=units.map(fold_map).fillna(-1).to_numpy()
    validation_region=(assignment==fold)&~holdout
    reference=validation_region|holdout
    lower=distance_lower_bound(grid,reference,spec)
    train=parent_train&~reference&(lower>=gap)
    test=parent_train&validation_region
    roles=np.full(len(grid),'outside_parent',dtype=object)
    roles[parent_train]='spatial_gap';roles[train]='train';roles[test]='test'
    roles[~grid.eligible.to_numpy()]='outside_support';roles[holdout]='holdout'
    positives=grid.cell_id.isin(positive_cells).to_numpy()
    train_units=set(units[train]);test_units=set(units[test])
    if train_units&test_units:raise AssertionError('Unidad compartida entre train/test.')
    if np.any(train&holdout) or (train.any() and lower[train].min()<gap):raise AssertionError('Separación inválida.')
    summary={'train_cells':int(train.sum()),'test_cells':int(test.sum()),
             'train_p_cells':int((train&positives).sum()),'test_p_cells':int((test&positives).sum()),
             'train_p_units':int(units[train&positives].nunique()),'test_p_units':int(units[test&positives].nunique()),
             'minimum_train_test_holdout_gap_lower_bound_m':float(lower[train].min()) if train.any() else None,
             'unit_overlap':0}
    return pd.DataFrame({'cell_id':grid.cell_id,'role':roles}),summary


def seal_stage(out,name,paths):
    write_json(out/f'{name}_manifest.json',records(out,paths))


def stage_exists(out,name):
    p=out/f'{name}_manifest.json'
    if not p.exists():return False
    verify(out,read_json(p));return True


def build_splits(root,out):
    cfg,grid,relations,spec,groupmap=context(root,out)
    if stage_exists(out,'splits'):return pd.read_csv(out/'split_summary.csv')
    positives,reviewed=choose_labels(grid,relations,cfg)
    positive_cells=set(positives.cell_id)
    columns=['deposit_id','district_id']
    if cfg['mode']=='diagnostic':columns.append(cfg['diagnostic_group_column'])
    # Agrupar todos los indicios conocidos permite conservar sus relaciones.
    sensitivity=[]
    for size in cfg['sensitivity_block_sizes_m']:
        units,_=connected_units(grid,relations,size,spec['resolution_m'],columns,groupmap)
        sensitivity.append({'block_size_m':size,'blocks':units.block_id.nunique(),'units':units.unit_id.nunique(),
            'units_with_selected_P':units.loc[units.cell_id.isin(positive_cells),'unit_id'].nunique(),
            'scope':'diagnostico de agrupación; no estima autocorrelación ni elige ganador'})
    design,links=connected_units(grid,relations,cfg['block_size_m'],spec['resolution_m'],columns,groupmap)
    units=design.unit_id
    ordered=sorted(units.unique(),key=lambda u:(seed_for(cfg['seed'],'reserve',u),u))
    if cfg['reserve_district_ids']:
        if groupmap is None:raise ValueError('Reserva por distrito requiere cartografía territorial.')
        existing=set(groupmap.district_id.dropna())
        if not set(cfg['reserve_district_ids'])<=existing:raise ValueError('Distrito de reserva no encontrado.')
        hold_cells=set(groupmap.loc[groupmap.district_id.isin(cfg['reserve_district_ids']),'cell_id'])
        reserved=set(design.loc[design.cell_id.isin(hold_cells),'unit_id'])
    else:
        n=max(1,int(round(len(ordered)*cfg['holdout_fraction'])))
        reserved=set(ordered[:n])
    holdout=units.isin(reserved).to_numpy()
    parent=grid.eligible.to_numpy()&~holdout
    development_units=units[~holdout]
    selected=None;attempts=[]
    for k in range(min(cfg['outer_folds'],development_units.nunique()),1,-1):
        foldmap=assign_fold(development_units,k,cfg['seed'],'outer')
        summaries=[]
        for fold in range(k):
            _,summary=split_membership(grid,units,holdout,parent,foldmap,fold,spec,cfg['spatial_gap_m'],positive_cells)
            summaries.append(summary)
        feasible=all(s['test_p_units']>=cfg['minimum_positive_units_test'] and s['train_p_units']>=cfg['minimum_positive_units_train'] for s in summaries)
        attempts.append({'outer_folds':k,'feasible':feasible})
        if feasible:selected=(k,foldmap);break
    if selected is None:
        raise ValueError('No hay al menos dos folds viables tras reserva/separación; revisar tamaño/etiquetas, no entrenar.')
    k,foldmap=selected
    design['holdout']=holdout;design['outer_fold']=units.map(foldmap).fillna(-1).astype(int)
    paths=[]
    def save(frame,name):
        p=out/name
        if p.suffix=='.parquet':atomic_parquet(frame,p)
        else:frame.to_csv(p,index=False,encoding='utf-8-sig')
        paths.append(p)
    save(design,'design/spatial_units.parquet');save(links,'group_links.csv')
    save(pd.DataFrame(sensitivity),'block_sensitivity.csv')
    save(positives.assign(protocol_role='P_candidate_proxy' if cfg['mode']=='diagnostic' else 'P_reviewed'),'design/selected_positive_records.parquet')
    plan=[];summary_rows=[]
    for outer in range(k):
        split,summary=split_membership(grid,units,holdout,parent,foldmap,outer,spec,cfg['spatial_gap_m'],positive_cells)
        split_id=f'outer_{outer:02d}'
        save(split,f'memberships/{split_id}.parquet')
        plan.append({'split_id':split_id,'level':'outer','outer_fold':outer,'inner_fold':None,'evaluation_role':'test'})
        summary_rows.append({'split_id':split_id,**summary})
        outer_train=split.role.eq('train').to_numpy()
        # Solo las unidades del entrenamiento externo participan en el diseño interno.
        available=units[outer_train].unique()
        inner_design=None
        for inner_k in range(min(cfg['inner_folds'],len(available)),1,-1):
            inner_map=assign_fold(available,inner_k,cfg['seed'],'inner',outer)
            parts=[split_membership(grid,units,holdout,outer_train,inner_map,j,spec,cfg['spatial_gap_m'],positive_cells) for j in range(inner_k)]
            if all(s['test_p_units']>=cfg['minimum_positive_units_test'] and s['train_p_units']>=cfg['minimum_positive_units_train'] for _,s in parts):
                inner_design=parts;break
        if inner_design is None:raise ValueError(f'Fold externo {outer} sin particiones internas viables.')
        for inner,(part,stats) in enumerate(inner_design):
            if not part.role.isin(['train','test']).to_numpy()[~outer_train].sum()==0:
                raise AssertionError('El diseño interno accede a datos externos.')
            split_id=f'outer_{outer:02d}_inner_{inner:02d}'
            save(part,f'memberships/{split_id}.parquet')
            plan.append({'split_id':split_id,'level':'inner','outer_fold':outer,'inner_fold':inner,'evaluation_role':'validation'})
            summary_rows.append({'split_id':split_id,**stats})
        print('Particiones externo/internas:',outer,flush=True)
    save(pd.DataFrame(summary_rows),'split_summary.csv')
    p=out/'split_plan.json';write_json(p,{'mode':cfg['mode'],'outer_folds':k,'attempts':attempts,'splits':plan,
        'reservation':'distritos con cierre de unidades' if cfg['reserve_district_ids'] else 'reserva geográfica diagnóstica, no distritos validados',
        'reserved_units':len(reserved),'holdout_cells':int((holdout&grid.eligible.to_numpy()).sum()),
        'holdout_not_used_for_fit_or_tuning':True});paths.append(p)
    seal_stage(out,'splits',paths)
    return pd.DataFrame(summary_rows)


def background_pool(grid,membership,positive_cells,buffer_m,resolution):
    if not grid.cell_id.equals(membership.cell_id):raise ValueError('Orden de celdas incompatible.')
    train=membership.role.eq('train').to_numpy()
    is_p=grid.cell_id.isin(positive_cells).to_numpy()&train
    positive=grid.loc[is_p].copy()
    # Solo P de entrenamiento: nunca coordenadas de prueba/reserva para vaciar U.
    eligible=train&~is_p
    if is_p.any():
        distance=cKDTree(grid.loc[is_p,['x_center','y_center']].to_numpy()).query(grid[['x_center','y_center']].to_numpy())[0]
        lower=np.maximum(0,distance-np.sqrt(2)*resolution)
        eligible &= lower>=buffer_m
    return positive,grid.loc[eligible].copy()


def stratified_u(pool,n,seed):
    """SRS por bloque, con probabilidad de inclusión explícita incluso si n<H."""
    if n<=0 or pool.empty:raise ValueError('Muestra U vacía solicitada.')
    pool=pool.sort_values('cell_id').reset_index(drop=True)
    n=min(int(n),len(pool));rng=np.random.default_rng(seed)
    grouped={key:part for key,part in pool.groupby('block_id',sort=True)}
    keys=list(grouped);H=len(keys)
    allocation=np.zeros(H,dtype=int);first_stage=np.ones(H)
    if n<H:
        chosen=rng.choice(H,size=n,replace=False);allocation[chosen]=1
        first_stage[:]=n/H
    else:
        sizes=np.array([len(grouped[k]) for k in keys]);allocation[:]=1
        area=np.array([grouped[k].land_area_m2.sum() for k in keys])
        remaining=n-H
        while remaining:
            capacity=sizes-allocation;active=capacity>0
            weights=np.where(active,area,0);target=remaining*weights/weights.sum()
            added=np.minimum(capacity,np.floor(target).astype(int))
            if added.sum()==0:
                # Redondeo determinista; todas las unidades ya tienen inclusión >0.
                candidates=np.flatnonzero(active)
                chosen=sorted(candidates,key=lambda i:(-target[i],keys[i]))[:remaining]
                added[chosen]=1
            allocation+=added;remaining-=int(added.sum())
    frames=[];design=[]
    for i,key in enumerate(keys):
        part=grouped[key];take=int(allocation[i]);prob=float(first_stage[i]*take/len(part)) if n>=H else float((n/H)/len(part))
        design.append({'block_id':key,'pool_cells':len(part),'sampled_cells':take,
                       'stratum_selection_probability':float(first_stage[i]),'cell_inclusion_probability':prob})
        if not take:continue
        sample=part.iloc[rng.choice(len(part),size=take,replace=False)].copy()
        sample['inclusion_probability']=prob
        sample['inverse_inclusion_weight']=1/prob
        sample['area_weight_m2']=sample.land_area_m2/prob
        frames.append(sample)
    result=pd.concat(frames,ignore_index=True)
    if len(result)!=n or not result.cell_id.is_unique:raise AssertionError('Muestreo sin reemplazo incoherente.')
    return result,pd.DataFrame(design)


def build_samples(root,out):
    cfg,grid,relations,spec,_=context(root,out)
    if stage_exists(out,'samples'):return pd.read_csv(out/'sample_summary.csv')
    if not stage_exists(out,'splits'):raise ValueError('Ejecutar 07 primero.')
    units=pd.read_parquet(out/'design/spatial_units.parquet')
    grid=grid.merge(units[['cell_id','block_id','unit_id']],on='cell_id',validate='one_to_one')
    positives,_=choose_labels(grid,relations,cfg);positive_cells=set(positives.cell_id)
    plans=read_json(out/'split_plan.json')['splits'];paths=[];summary=[]
    role='P_candidate_proxy' if cfg['mode']=='diagnostic' else 'P_reviewed'
    for item in plans:
        split_id=item['split_id'];membership=pd.read_parquet(out/f'memberships/{split_id}.parquet')
        p,pool=background_pool(grid,membership,positive_cells,cfg['background_buffer_m'],spec['resolution_m'])
        if p.empty or pool.empty:raise ValueError(f'{split_id}: P o U de entrenamiento vacío.')
        p=p[['cell_id','block_id','unit_id','land_area_m2']].copy()
        p['sample_role']=role;p['sample_class']=1
        p['inclusion_probability']=1.;p['inverse_inclusion_weight']=1.;p['area_weight_m2']=np.nan
        # P=1 es pertenencia a la muestra observada; no estima probabilidad poblacional.
        for ratio in cfg['ratios_u_to_p']:
            for repetition in range(cfg['realizations']):
                sample_seed=seed_for(cfg['seed'],'background',split_id,ratio,repetition)
                u,allocation=stratified_u(pool,len(p)*ratio,sample_seed)
                u=u[['cell_id','block_id','unit_id','land_area_m2','inclusion_probability','inverse_inclusion_weight','area_weight_m2']].copy()
                u['sample_role']='U_unlabelled';u['sample_class']=0
                sample=pd.concat([p,u],ignore_index=True)
                sample['mode']=cfg['mode'];sample['training_allowed']=cfg['mode']=='validated'
                tag=f'{split_id}_ratio{ratio}_rep{repetition:02d}'
                path=out/f'samples/{tag}.parquet';atomic_parquet(sample,path);paths.append(path)
                path=out/f'samples/{tag}_allocation.parquet';atomic_parquet(allocation,path);paths.append(path)
                if not set(sample.cell_id)<=set(membership.loc[membership.role.eq('train'),'cell_id']):raise AssertionError('Fuga fuera de entrenamiento.')
                if set(u.cell_id)&set(p.cell_id):raise AssertionError('P incluido en U.')
                summary.append({'sample_id':tag,'split_id':split_id,'level':item['level'],'ratio_requested':ratio,
                    'realization':repetition,'seed':str(sample_seed),'n_P':len(p),'n_U':len(u),
                    'available_U':len(pool),'requested_U':len(p)*ratio,'ratio_realized':len(u)/len(p),
                    'pool_capped':len(u)<len(p)*ratio,'mode':cfg['mode']})
        print('Muestras P/U:',split_id,flush=True)
    table=pd.DataFrame(summary);p=out/'sample_summary.csv';table.to_csv(p,index=False,encoding='utf-8-sig');paths.append(p)
    p=out/'learning_contract.json';write_json(p,{
        'mode':cfg['mode'],'reference':'P frente a U; U no significa ausencia de oro',
        'baseline':'realización 0 de cada ratio; elegir ratio solo dentro del bucle interno',
        'pu_alternative':'bagging de realizaciones U; mismos P y marco de evaluación por split',
        'aggregation':'media de scores de las realizaciones; no probabilidad absoluta de oro',
        'evaluation':'todas las celdas elegibles con role=test en membresía; no muestrear el test',
        'holdout':'no se generan muestras para entrenar/ajustar sobre la reserva',
        'weights':'inversos de inclusión de U, no class_weight ni probabilidad de observación de P',
        'preprocessing':'imputación, codificación, selección y escalado se ajustan en cada train interno',
        'model_fitting':'corresponde a fase F; aquí solo contratos y diseños',
        'automatic_scar_or_prevalence_assumption':False});paths.append(p)
    seal_stage(out,'samples',paths)
    return table


def finish_run(root,out):
    cfg,grid,relations,spec,groupmap=context(root,out)
    if (out/'outputs_manifest.json').exists():
        verify(out,read_json(out/'outputs_manifest.json'));return read_json(out/'control_cierre.json')
    if not stage_exists(out,'splits') or not stage_exists(out,'samples'):raise ValueError('Faltan etapas E.')
    summary=pd.read_csv(out/'split_summary.csv');samples=pd.read_csv(out/'sample_summary.csv')
    gate=readiness(root,cfg,grid,relations,groupmap)
    training_allowed=cfg['mode']=='validated' and gate['ready_for_scientific_training']
    control={'estado_ejecucion':'completada','mode':cfg['mode'],'fase_e_cientifica_cerrada':training_allowed,
        'training_allowed':training_allowed,'prediction_allowed':False,'eligible_cells':int(grid.eligible.sum()),
        'reviewed_positive_cells':gate['reviewed_positive_cells'],
        'selected_protocol_positive_cells':gate['diagnostic_or_selected_positive_cells'],
        'outer_folds':read_json(out/'split_plan.json')['outer_folds'],'split_designs':len(summary),
        'sample_designs':len(samples),'minimum_gap_lower_bound_m':float(summary.minimum_train_test_holdout_gap_lower_bound_m.min()),
        'reasons_not_ready':gate['reasons']}
    write_json(out/'control_cierre.json',control)
    files=sorted(p for p in out.rglob('*') if p.is_file() and p.name!='outputs_manifest.json' and not p.name.startswith('.'))
    write_json(out/'outputs_manifest.json',records(out,files))
    return control


def assert_ready_for_training(root,out):
    context(root,out)
    verify(out,read_json(out/'outputs_manifest.json'))
    control=read_json(out/'control_cierre.json')
    if not control.get('training_allowed'):
        raise ValueError('Diseño diagnóstico/no aprobado: no usar como conjunto validado para entrenamiento.')
    return True
