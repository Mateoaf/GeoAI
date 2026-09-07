from pathlib import Path
import sqlite3,json,pandas as pd,sys,zipfile,xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8')
r=Path(__file__).resolve().parents[1]; o=r/'informes/auditoria_2026-09-05'; out={}
for p in r.glob('*.csv'):
 d=pd.read_csv(p,low_memory=False)
 out[p.name]={'rows':len(d),'columns':list(d.columns),'unique_ids':{c:int(d[c].nunique()) for c in ['OBJECTID','Codigo_indicio','ESRI_OID'] if c in d}}
for p in r.glob('*.gpkg'):
 con=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True)
 for (tn,) in con.execute('select table_name from gpkg_contents'):
  cols=[x[1] for x in con.execute('pragma table_info("'+tn+'")')]
  q={c:con.execute('select count(distinct "'+c+'") from "'+tn+'"').fetchone()[0] for c in ['OBJECTID','Codigo_indicio','ESRI_OID'] if c in cols}
  out[p.name]={'unique_ids':q}
  for col in ['TIPO','DESC_LINE']:
   if col in cols: out[p.name][col]=dict(con.execute('select "'+col+'",count(*) from "'+tn+'" group by "'+col+'"').fetchall())
  if p.name=='IndiciosII.gpkg':
   d=pd.read_sql_query('select * from "'+tn+'"',con).drop(columns='geom')
   au=d[d.Sustancia.str.contains(r'\b(?:oro|au)\b',case=False,na=False,regex=True)]
   out[p.name].update(au_records=len(au),au_substances=au.Sustancia.value_counts().to_dict(),au_morphology=au.Morfologia.fillna('NULL').value_counts().to_dict(),au_province=au.Provincia.fillna('NULL').value_counts().to_dict(),xy_sample=d[['X','Y']].head().to_dict('records'))
 con.close()
(o/'tablas_comprobaciones.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str),encoding='utf8')
for k,v in out.items(): print(k,{a:b for a,b in v.items() if a not in ['columns','TIPO','DESC_LINE']})
