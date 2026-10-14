"""Exact user-authorized banner amendment; historical product/approval bytes stay sealed."""
from pathlib import Path
import copy, hashlib, json
AMENDMENT_SHA256 = 'e18d39fae0fe83105ccb509b334218656ccfa2ab05d2e9c49643474eae139019'
VARIANTS = ('message','budget','consultation')
def load_amendment(root):
 p=Path(root)/'src/data/common-banner-phone-amendment.json'
 assert p.is_file() and not p.is_symlink(), 'Banner amendment missing/unsafe'
 raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==AMENDMENT_SHA256, 'Banner amendment byte drift'
 a=json.loads(raw);assert set(a['assets'])==set(VARIANTS) and a['phone']=='1844-0644'
 assert a['productPhotosChanged'] is False and a['historicalApprovalSealsChanged'] is False
 for variant,v in a['assets'].items():
  assert v['file']=='flower-'+variant+'.webp' and v['runtimePath']=='public/images/shared-banners/'+v['file']
  assert v['dimensions']==[1774,887] and '1844-0644' in v['alt']
 return a

def effective_assets(root, sealed_assets):
 a=load_amendment(root);assets=copy.deepcopy(sealed_assets)
 assert len(assets)==11 and len([v for v in assets if v['kind']=='actual-sale-product'])==8
 for variant,v in a['assets'].items():
  rows=[x for x in assets if x['proposedRuntimePath']==v['runtimePath']];assert len(rows)==1
  row=rows[0];assert row['kind']!='actual-sale-product'
  assert row['snapshot']['sha256']==v['previousSha256'] and row['snapshot']['bytes']==v['previousBytes']
  row['snapshot']['sha256']=v['sha256'];row['snapshot']['bytes']=v['bytes'];row['alt']=v['alt']
 assert [v for v in assets if v['kind']=='actual-sale-product']==[v for v in sealed_assets if v['kind']=='actual-sale-product']
 return assets
