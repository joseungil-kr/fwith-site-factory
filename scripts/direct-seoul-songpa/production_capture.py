"""Capture the same-run pinned Songpa production artifact; never build, deploy or attach a host."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from preview_qa import ROOT, ROUTE_ORDER, require
from production_build import source,load
REVISION=load()[0]["sourceRevision"]
from reused import manifest, write_json


def seal(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    files={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name!='artifact-manifest.json'}
    write_json(out/'artifact-manifest.json',{'sourceRevision':REVISION,'files':files,'pixelReview':'pending','publicationAuthorized':False,'publicHTTPVerified':False})


def capture_inputs(root):
    root=Path(root)
    runtime=json.loads((root/'src/data/songpa-runtime.json').read_text())
    pages=[next(p for p in runtime['pages'] if p['path']==route) for route in ROUTE_ORDER]
    require([p['path'] for p in pages]==ROUTE_ORDER,'pinned_page_order_changed')
    spec={'banners':{},'removedCaption':'AI로 제작한 감성 이미지입니다.','common':runtime['common'],'products':runtime['products']}
    for banner in runtime['common']['banners']:
        asset=next(a for a in runtime['assets'] if a.get('id')==banner['id'])
        require(asset['path']=='public/images/shared-banners/'+banner['assetName']+'.webp','banner_asset_path')
        spec['banners'][banner['id']]={'file':banner['assetName']+'.webp','sha256':asset['sha256'],'alt':banner['alt']}
    for asset in runtime['assets']:
        require(asset['path'].startswith('public/images/') and '..' not in Path(asset['path']).parts,'asset_path')
        require(hashlib.sha256((root/'dist'/asset['path'].removeprefix('public/')).read_bytes()).hexdigest()==asset['sha256'],'image_asset_changed')
    return pages,spec


def capture(checkout,out):
    root=Path(checkout)/ROOT;out=Path(out)
    before=source(checkout,'postbuild',os.environ);write_json(out/'source-before-capture.json',before)
    pages,spec=capture_inputs(root)
    spec["releaseMode"]="production"
    write_json(out/'exact-ui-inputs.json',{'pages':pages,'spec':spec})
    from browser_rendering import inspect
    failures=[]
    try:
        inspect(root/'dist',out,pages,REVISION,spec)
    except Exception as error:
        failures.append({'phase':'browser','type':type(error).__name__,'message':str(error)})
    try:
        after=source(checkout,'postbuild',os.environ)
        write_json(out/'source-after-capture.json',after)
        require(before==after,'source_or_output_changed_during_capture')
    except Exception as error:
        failures.append({'phase':'post-capture-integrity','type':type(error).__name__,'message':str(error)})
    write_json(out/'capture-status.json',{'status':'machine-qa-failed' if failures else 'captured-awaiting-independent-pixel-review',
               'failures':failures,'sourceRevision':REVISION,'pixelReview':'pending','publicHTTPVerified':False,'publicationAuthorized':False})
    if failures:
        report=json.loads((out/'report.json').read_text()) if (out/'report.json').is_file() else {}
        report.update({'status':'machine-qa-failed','controllerFailures':failures,'sourceRevision':REVISION,
                       'pixelReview':'pending','publicHTTPVerified':False,'publicationAuthorized':False})
        write_json(out/'report.json',report)
        raise RuntimeError(json.dumps(failures))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--checkout');p.add_argument('--output',required=True);p.add_argument('--seal',action='store_true');a=p.parse_args()
    if a.seal:seal(a.output)
    else:
        require(bool(a.checkout),'checkout_required')
        try:capture(a.checkout,a.output)
        finally:seal(a.output)
