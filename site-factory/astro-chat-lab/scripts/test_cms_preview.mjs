import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";

const script=readFileSync("public/admin/preview.js","utf8");
const config=readFileSync("public/admin/config.yml","utf8");
const siteOrigin="https://astro-chat-lab-qa.joseungil.workers.dev";

function previewFor(markdown,getAsset,options={}){
  let component;
  const h=(tag,props,...children)=>({tag,props:props||{},children});
  const window={
    location:{origin:siteOrigin},
    setTimeout: options.setTimeout,
    h,
    CMS:{registerPreviewTemplate(name,fn){
      assert.equal(name,"posts");
      component=fn;
    }},
  };
  runInNewContext(script,{window,URL,console});
  assert.equal(typeof component,"function","PostsPreview must register in Decap");
  const props={
    entry:{get(key){
      if(key!=="data")return undefined;
      return {get(name){
        const vals={title:"3",description:"333",pubDatetime:"2026-10-09T15:49:00+09:00",body:markdown};
        return vals[name];
      }};
    }},
    getAsset:getAsset||(()=>null)
  };
  return component(props);
}
function flatten(tree,what,result=[]){
  if(!tree)return result;
  if(Array.isArray(tree)){for(const child of tree)flatten(child,what,result);return result;}
  if(typeof tree!=="object")return result;
  if(tree.tag===what)result.push(tree);
  for(const child of tree.children||[])flatten(child,what,result);
  return result;
}

test("Editor excludes code-block and H1 while keeping image, text and raw Markdown",()=>{
  assert.match(config,/editor_components: \["image"\]/);
  assert.match(config,/modes: \["rich_text", "raw"\]/);
  assert.match(config,/buttons: \["bold", "italic", "link", "heading-two", "heading-three", "quote", "bulleted-list", "numbered-list"\]/);
  assert.match(config,/widget: "richtext"/);
  assert.match(config,/public_folder: "\/uploads"/);
});

test("Saved Korean uploaded images render as same-origin absolute HTTP URLs",()=>{
  const path="/uploads/학교-앞-콜팝-판매-한장-정리.png";
  const document=previewFor("## 사진 확인\n![이미지테스트]("+path+' "제목")\n\n이미지 뒤 일반 문단');
  const imgs=flatten(document,"img");
  assert.equal(imgs.length,1);
  assert.equal(imgs[0].props.src,new URL(path,siteOrigin).href);
  assert.equal(imgs[0].props.alt,"이미지테스트");
  assert.equal(imgs[0].props.title,"제목");
  assert.equal(flatten(document,"figure").length,1);
  const texts=flatten(document,"p").flatMap(p=>p.children.map(c=>String(c))).join("|");
  assert.match(texts,/이미지 뒤 일반 문단/);
  assert.equal(flatten(document,"div").some(x=>x.props.role==="heading"),true);
});

test("Uncommitted CMS blob preview is accepted only for its own admin origin",()=>{
  const path="/uploads/new-editor-picture.jpg";
  const blob="blob:"+siteOrigin+"/3d167315-40ee-46b4-9e87-321cb67fd2f4";
  const tree=previewFor("![임시 이미지]("+path+")",()=>({toString:()=>blob}));
  assert.equal(flatten(tree,"img")[0].props.src,blob);
  const foreign=previewFor("![임시 이미지]("+path+")",()=>({toString:()=>"blob:https://evil.example/4"}));
  assert.equal(flatten(foreign,"img")[0].props.src,siteOrigin+path);
});

test("A missing CMS preview image retries the saved URL and never shows a broken icon",()=>{
  const blob="blob:"+siteOrigin+"/f2e4de0c-5b12-4da3-9edc-105879db61b8";
  const tree=previewFor("![사진](/uploads/file.jpg)",()=>({toString:()=>blob}));
  const img=flatten(tree,"img")[0];
  const alt={hidden:true};
  const el={src:blob,dataset:{},hidden:false,nextSibling:alt};
  img.props.onError({currentTarget:el});
  assert.equal(el.src,siteOrigin+"/uploads/file.jpg");
  assert.equal(el.dataset.triedPublic,"1");
  img.props.onError({currentTarget:el});
  assert.equal(el.hidden,true);
  assert.equal(alt.hidden,false);
});

test("Non-local media URLs cannot load an untrusted external origin",()=>{
  const tree=previewFor("![추적 이미지](https://evil.example/tracker.png)\n![더미](javascript:alert)",()=>null);
  assert.equal(flatten(tree,"img").length,0);
  const texts=flatten(tree,"p").flatMap(p=>p.children).map(x=>String(x));
  assert.equal(texts.filter(t=>t.includes("/uploads 이미지 주소가 아닙니다.")).length,2);
});

test("Existing Decap code blocks and paragraphs remain visible in read-only preview",()=>{
  const markdown="~~~\nconst x = 1\n~~~\n\n![테스트](/uploads/how-to.jpg)\n\n문장 하나 더.";
  const tree=previewFor(markdown);
  assert.equal(flatten(tree,"pre").length,1);
  assert.equal(flatten(tree,"img").length,1);
  assert.equal(flatten(tree,"p").some(p=>p.children.includes("문장 하나 더.")),true);
});


test("Newly uploaded media is retrieved by filename, not the unavailable /uploads URL",()=>{
  const filename="새-테스트-사진.png";
  const stagedBlob="blob:"+siteOrigin+"/3e900f4d-b90f-428c-8324-8ea149241eb8";
  const args=[];
  const body="![사진](/uploads/"+filename+")";
  const tree=previewFor(body,name=>{
    args.push(name);
    return {path:"site-factory/astro-chat-lab/public/uploads/"+name,toString:()=>stagedBlob};
  });
  const imgs=flatten(tree,"img");
  assert.equal(imgs.length,1);
  assert.equal(imgs[0].props.src,stagedBlob);
  assert.deepEqual(args,[filename],"Decap staging is keyed by repo media path + basename");
});

test("Decap's empty.svg placeholder is not mistaken for a selected image",()=>{
  const img=flatten(previewFor("![사진](/uploads/new.png)",()=>({
    path:"empty.svg",toString:()=>"blob:"+siteOrigin+"/empty-file"
  })),"img")[0];
  assert.equal(img.props.src,siteOrigin+"/uploads/new.png");
});

test("Asynchronously staged images are picked up without publishing or reloading",()=>{
  const filename="초안-사진.jpg";
  const url=new URL("/uploads/"+filename,siteOrigin).href;
  const blob="blob:"+siteOrigin+"/51ac57dd-983f-4f9c-93b8-c931ab409bf8";
  let ready=false;
  const timers=[],reads=[];
  const preview=previewFor("![사진](/uploads/"+filename+")",name=>{
    reads.push(name);
    if(!ready)return {path:"empty.svg",toString:()=>blob};
    return {path:"site-factory/astro-chat-lab/public/uploads/"+filename,toString:()=>blob};
  },{setTimeout:fn=>{timers.push(fn);return timers.length;}});
  const img=flatten(preview,"img")[0];
  const warning={hidden:true,style:{display:"none"}};
  const el={src:url,dataset:{},nextSibling:warning,hidden:false,style:{display:"block"},isConnected:true};
  img.props.onError({currentTarget:el});
  assert.equal(timers.length,1);
  assert.equal(el.dataset.polling,"1");
  ready=true;
  timers.shift()();
  assert.equal(el.src,blob,"Retry should switch to new staged object URL");
  assert.equal(el.dataset.polling,"0");
  img.props.onLoad({currentTarget:el});
  assert.equal(el.hidden,false);
  assert.equal(el.style.display,"block");
  assert.equal(warning.hidden,true);
  assert.equal(warning.style.display,"none");
  assert.ok(reads.every(name=>name===filename));
});

test("Old pending timers do not hide an image that already loaded",()=>{
  const filename="file.jpg";
  const url=siteOrigin+"/uploads/"+filename;
  const timers=[];
  const tree=previewFor("![사진](/uploads/"+filename+")",()=>null,{
    setTimeout:fn=>{timers.push(fn);return timers.length;}
  });
  const img=flatten(tree,"img")[0];
  const warning={hidden:true,style:{display:"none"}};
  const el={src:url,dataset:{},nextSibling:warning,hidden:false,style:{display:"block"},isConnected:true};
  img.props.onError({currentTarget:el});
  assert.equal(timers.length,1);
  img.props.onLoad({currentTarget:el});
  const queued=timers.shift();
  queued();
  assert.equal(timers.length,0);
  assert.equal(el.hidden,false);
  assert.equal(warning.hidden,true);
  assert.equal(warning.style.display,"none");
});

test("Warning stays hidden while the image loads and appears only after genuine failure",()=>{
  const tree=previewFor("![사진](/uploads/not-ready.png)",()=>null);
  const img=flatten(tree,"img")[0];
  const status=flatten(tree,"small")[0];
  assert.equal(status.props.hidden,true);
  assert.equal(status.props.style.display,undefined);
  const note={hidden:true,style:{display:"none"}};
  const el={src:siteOrigin+"/uploads/not-ready.png",dataset:{},nextSibling:note,
    isConnected:false,hidden:false,style:{display:"block"}};
  img.props.onLoad({currentTarget:el});
  assert.equal(note.hidden,true);
  img.props.onError({currentTarget:el});
  assert.equal(el.hidden,true);
  assert.equal(el.style.display,"none");
  assert.equal(note.hidden,false);
  assert.equal(note.style.display,"block");
});
