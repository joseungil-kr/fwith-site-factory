"""Capture the same-run pinned Gangnam preview; never build, deploy or attach a host."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from preview_qa import ROOT, REVISION, ROUTE_ORDER, require, source
from reused import manifest, write_json


def seal(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    files={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file() and p.name!='artifact-manifest.json'}
    write_json(out/'artifact-manifest.json',{'sourceRevision':REVISION,'files':files,'pixelReview':'pending','publicationAuthorized':False,'publicHTTPVerified':False})


def capture(checkout,out):
    root=Path(checkout)/ROOT;out=Path(out)
    before=source(checkout,'postbuild',os.environ);write_json(out/'source-before-capture.json',before)
    pages=json.loads((root/'src/data/pages.json').read_text())
    require(['/','/regions/']+[p['url'] for p in pages]+['/404.html']==ROUTE_ORDER,'pinned_page_order_changed')
    amendment=json.loads((root/'src/data/common-banner-phone-amendment.json').read_text())
    spec={'banners':amendment['assets'],'removedCaption':amendment['removedVisibleCaption']}
    for banner in spec['banners'].values():
        require(hashlib.sha256((root/'dist/images/shared-banners'/banner['file']).read_bytes()).hexdigest()==banner['sha256'],'banner_asset_changed')
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
