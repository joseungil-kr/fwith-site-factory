"""Mutations of real N2 compiled output; no browser or external action."""
import json,shutil,tempfile,unittest,re
from pathlib import Path
from qa_yeongdeungpo import inspect
class Mutations(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.r=Path(self.tmp.name)
  for p in ['src/data','dist']:shutil.copytree(Path.cwd()/p,self.r/p)
  self.detail=self.r/'dist/regions/yeongdeungpo-funeral-wreath/index.html';self.directory=self.r/'dist/regions/index.html'
 def tearDown(self):self.tmp.cleanup()
 def mutate(self,f,old,new):
  s=f.read_text();self.assertIn(old,s);f.write_text(s.replace(old,new,1))
 def fail(self,pattern):
  with self.assertRaisesRegex(AssertionError,pattern):inspect(self.r,write=False)
 def test_shared_caption_reintroduced(self):
  self.mutate(self.detail,'</figure>','<figcaption>꽃이랑 공통 안내 이미지 · 실제 판매상품 사진이 아닌 AI 생성 이미지입니다.</figcaption></figure>');self.fail('caption reintroduced')
 def test_banner_overlay_bytes(self):
  f=self.r/'src/data/shared-banner-requested-change.json';f.write_text(f.read_text()+' ');self.fail('overlay byte drift')
 def test_banner_bytes(self):
  f=self.r/'dist/images/shared-banners/flower-message.webp';f.write_bytes(f.read_bytes()+b' ');self.fail('Banner byte drift')
 def test_banner_alt(self):
  self.mutate(self.detail,' 전화 1844-0644.',' 전화 1844-0645.');self.fail('Banner alt drift')
 def test_clean(self):inspect(self.r,write=False)
 def test_copy_bytes(self):
  f=self.r/'src/data/yeongdeungpo-copy.json';f.write_text(f.read_text()+' ');self.fail('copy byte drift')
 def test_h3_anchor_level(self):
  self.mutate(self.detail,'<h3 id="yeouido-stmary">','<h2 id="yeouido-stmary">');self.fail('anchor level/text')
 def test_broken_fragment(self):
  self.mutate(self.directory,'#yeouido-stmary','#wrong-anchor');self.fail('Broken fragment')
 def test_duplicate_anchor(self):
  self.mutate(self.detail,'</main>','<h3 id="yeouido-stmary">duplicate</h3></main>');self.fail('Duplicate HTML id')
 def test_extra_standalone_route(self):
  f=self.r/'dist/regions/held/index.html';f.parent.mkdir();f.write_text(self.detail.read_text());self.fail('Unexpected standalone')
 def test_admin_facility_link(self):
  s=self.directory.read_text();s,n=re.subn(r'(<li data-administrative-unit="[^"]+">)',r'\1<a href="/regions/yeongdeungpo-funeral-wreath/#kangnam-hallym">강남성심</a>',s,count=1);self.assertEqual(n,1);self.directory.write_text(s);self.fail('must not imply')
 def test_admin_geography_drift(self):
  self.mutate(self.directory,'<strong>영등포본동</strong>:','<strong>가상의동</strong>:');self.fail('relation text drift')
 def test_policy_exception_missing(self):
  self.mutate(self.detail,'결제 후 배송이 불가능하거나 재고가 없어 진행하지 못하면 전액 환불한다는 안내도 있습니다.','');self.fail('Missing or changed approved body')
 def test_source_scope_warning_missing(self):
  self.mutate(self.detail,'개별 장례의 현재 빈소와 수령 조건을 나타내는 자료는 아닙니다.','');self.fail('Source limitation missing')
 def test_image_dimension(self):
  self.mutate(self.detail,'width="500" height="500"','width="500" height="499"');self.fail('Wrong product dimensions')
if __name__=='__main__':unittest.main()
