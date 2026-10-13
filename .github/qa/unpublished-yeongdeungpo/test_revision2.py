"""Socket-free regressions for independent-review REVISE findings."""
import copy,json,subprocess,unittest
from adapter import assert_focus, assert_footer_content, screenshot_selection
from run_bound_capture import FOOTER_CONTENT_SELECTOR, RENDER_SNAPSHOT, FOCUS_FACTS

class Revision2Tests(unittest.TestCase):
    def footer(self):
        items=[{'tag':'STRONG','text':'꽃이랑','visible':True,'left':22,'right':140,'top':600,'bottom':620,'hitTests':[True]*9},
               {'tag':'A','text':'전화 상담','visible':True,'left':150,'right':220,'top':600,'bottom':620,'hitTests':[True]*9},
               {'tag':'A','text':'공식몰','visible':True,'left':22,'right':100,'top':628,'bottom':648,'hitTests':[True]*9}]
        return {'visible':True,'width':276,'height':48,'left':22,'right':298,'top':600,'bottom':648,'safeTop':62,'safeBottom':682,'viewportWidth':320,'hitTests':[True]*9,
            'footerContent':{'selector':'footer > div','shellBottom':740,'shellPaddingBottom':92,'contentBottom':648,'barTop':682,'barVisible':True,'items':items}}
    def test_padded_shell_is_not_hidden_content(self):
        facts=self.footer()
        with self.assertRaisesRegex(AssertionError,'Target clipped'):assert_focus({**facts,'bottom':740,'height':140})
        # Original source reserves 34px + 58px inside the footer. Shell extends
        # beneath the fixed bar while actual text/link content remains above it.
        assert_footer_content(facts)
        self.assertGreater(facts['footerContent']['shellBottom'],facts['safeBottom'])
    def test_footer_selector_targets_content_only(self):
        self.assertEqual(FOOTER_CONTENT_SELECTOR,'footer > div')
        self.assertIn('shellPaddingBottom',FOCUS_FACTS)
        self.assertIn('items:[...el.children]',FOCUS_FACTS)
    def test_actual_footer_content_overlap_rejected(self):
        facts=self.footer();facts['bottom']=700;facts['footerContent']['contentBottom']=700
        with self.assertRaises(AssertionError):assert_footer_content(facts)
    def test_footer_child_text_overlap_rejected(self):
        facts=self.footer();facts['footerContent']['items'][2]['bottom']=701
        with self.assertRaisesRegex(AssertionError,'text/link overlaps'):assert_footer_content(facts)
    def test_footer_hidden_or_occluded_link_rejected(self):
        for key,value in [('visible',False),('hitTests',[True,False]),('text',''),('right',325)]:
            facts=self.footer();facts['footerContent']['items'][1][key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):assert_footer_content(facts)
    def test_footer_wrapper_and_boundary_evidence_required(self):
        for key,value in [('selector','footer'),('contentBottom',600),('barTop',740),('items',[])]:
            facts=self.footer();facts['footerContent'][key]=value
            with self.subTest(key=key),self.assertRaises(AssertionError):assert_footer_content(facts)
    def fixture(self):
        return {'tag':'FIGURE','text':'공통 안내 이미지 · AI 생성 이미지','box':{'left':10,'top':100,'width':300,'height':180},'css':{'display':'block','opacity':'1','overflow':'hidden'},'children':[
            {'tag':'IMG','text':'','box':{'left':10,'top':100,'width':300,'height':150},'css':{'object-fit':'fill','object-position':'50% 50%','filter':'none'},'src':'http://127.0.0.1:8080/images/shared-banners/flower-message.webp','alt':'꽃으로 전하는 마음','naturalWidth':1774,'naturalHeight':887,'complete':True},
            {'tag':'FIGCAPTION','text':'공통 안내 이미지 · AI 생성 이미지','box':{'left':10,'top':254,'width':300,'height':24},'css':{'font-size':'12px','line-height':'18px','color':'rgb(1, 2, 3)','padding-top':'4px','opacity':'1','visibility':'visible'}}]}
    def snapshots(self,fixtures):
        # Executes the SAME JS used by the deferred browser against a tiny DOM
        # fixture, without Chromium, a page, sockets, requests or source edits.
        harness=r'''
const snapshots=JSON.parse(process.argv[1]),fn=(new Function('return ('+process.argv[2]+')'))();
global.getComputedStyle=(node,pseudo=null)=>{const props=pseudo?(node.raw.pseudo?.[pseudo]||{content:'none'}):(node.raw.css||{});const a=Object.keys(props);a.getPropertyValue=k=>props[k]||'';a.content=props.content;return a;};
function make(raw){const n={raw,tagName:raw.tag,innerText:raw.text||'',src:raw.src,currentSrc:raw.src,alt:raw.alt,naturalWidth:raw.naturalWidth,naturalHeight:raw.naturalHeight,complete:raw.complete,children:(raw.children||[]).map(make)};
n.getBoundingClientRect=()=>raw.box;n.checkVisibility=()=>raw.visible!==false;n.querySelectorAll=()=>n.children.flatMap(c=>[c,...c.querySelectorAll('*')]);return n;}
process.stdout.write(JSON.stringify(snapshots.map(s=>fn(make(s)))));
'''
        proc=subprocess.run(['node','-e',harness,json.dumps(fixtures,ensure_ascii=False),RENDER_SNAPSHOT],capture_output=True,text=True,check=True)
        return [json.dumps(x,sort_keys=True,ensure_ascii=False) for x in json.loads(proc.stdout)]
    def rows(self,signatures):
        return [{'width':320,'route':route,'label':'banner-message','issues':[],'facts':{'width':300,'height':180,'renderSignature':signature}}for route,signature in zip(['/','/regions/yeongdeungpo-funeral-wreath/'],signatures)]
    def test_identical_subtree_at_different_scroll_position_deduplicates(self):
        a=self.fixture();b=copy.deepcopy(a)
        for n in [b,*b['children']]:n['box']['top']+=200
        signatures=self.snapshots([a,b]);self.assertEqual(signatures[0],signatures[1])
        self.assertEqual(len(screenshot_selection(self.rows(signatures))),1)
    def test_caption_font_line_height_color_padding_changes_add_evidence(self):
        for key,value in [('font-size','18px'),('line-height','30px'),('color','rgb(255, 0, 0)'),('padding-top','16px'),('opacity','0.5'),('visibility','hidden'),('filter','blur(2px)')]:
            a=self.fixture();b=copy.deepcopy(a);b['children'][1]['css'][key]=value
            signatures=self.snapshots([a,b])
            with self.subTest(key=key):
                self.assertNotEqual(signatures[0],signatures[1]);self.assertEqual(len(screenshot_selection(self.rows(signatures))),2)
    def test_caption_relative_bounds_and_image_styles_add_evidence(self):
        a=self.fixture();b=copy.deepcopy(a);b['children'][1]['box']['width']=299
        c=copy.deepcopy(a);c['children'][0]['css']['object-fit']='cover'
        d=copy.deepcopy(a);d['children'][0]['css']['filter']='grayscale(1)'
        baseline,*changed=self.snapshots([a,b,c,d])
        for value in changed:self.assertNotEqual(baseline,value)
    def test_footer_descendant_link_style_changes_add_evidence(self):
        a=self.fixture();a['tag']='DIV';a['children'][0]={'tag':'A','text':'공식몰','box':{'left':10,'top':100,'width':80,'height':24},'css':{'font-size':'14px','color':'gold','text-decoration-line':'none'}}
        b=copy.deepcopy(a);b['children'][0]['css']['color']='white'
        c=copy.deepcopy(a);c['children'][0]['box']['top']+=8
        signatures=self.snapshots([a,b,c]);self.assertNotEqual(signatures[0],signatures[1]);self.assertNotEqual(signatures[0],signatures[2])
        rows=self.rows(signatures[:2])
        for row in rows:row['label']='footer'
        self.assertEqual(len(screenshot_selection(rows)),2)
    def test_visible_pseudo_content_changes_add_evidence(self):
        a=self.fixture();b=copy.deepcopy(a);b['children'][1]['pseudo']={'::before':{'content':'"주의"','color':'red'}}
        x,y=self.snapshots([a,b]);self.assertNotEqual(x,y)

if __name__=='__main__':unittest.main()
