"""Boseong output validator, delegated to the pinned accepted source50 adapter."""
from pathlib import Path
import os,sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'production-release'))
import production_adapter as adapter
ORIGIN='https://boseong.fwith.kr'
FILES={'index.html':'/','404.html':'/404.html'}
CONTRACT=adapter.read_contract()
PROOF={'origin':ORIGIN,'path':CONTRACT['dedicatedPublicProof']['path'],'sha256':CONTRACT['dedicatedPublicProof']['sha256']}
def inspect_dist(dist,mode,proof=None):
    assert mode['mode']=='production' and mode['indexable'] is True and mode['origin']==ORIGIN
    assert proof==PROOF
    checkout=Path(os.environ.get('BOSEONG_SOURCE_CHECKOUT','source'))
    source=checkout/'site-factory/boseong-flower'
    result=adapter.validate(source,Path(dist),mode['revision'])
    return {'files':result['files'],'sitemapUrls':[ORIGIN+'/'],'notFoundProbe':{'path':'/.boseong-release-missing-'+mode['revision']+'/','expectedStatus':404,'bodySha256':result['files']['404.html']}}
