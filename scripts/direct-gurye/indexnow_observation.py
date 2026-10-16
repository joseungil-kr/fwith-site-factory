"""Bounded observations for the existing one-host IndexNow POST transport.

Same request serialization/headers/timeout/no-redirect semantics as the pinned
helper. No new submission/retry loop. Unknown response strings are withheld from
artifacts; hashes/length/status remain. Request bodies contain only approved public data.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re
from urllib.error import HTTPError
from http.client import IncompleteRead
from urllib.request import Request,build_opener

ROOT=Path('indexnow-wire-observations')
CAPTURE_LIMIT=4096
PUBLIC_KEY='cc583d309cec4f73ff7832d6a7d7b36f'
EXPECTED={'host':'gurye.fwith.kr','key':PUBLIC_KEY,'keyLocation':'https://gurye.fwith.kr/'+PUBLIC_KEY+'.txt','urlList':['https://gurye.fwith.kr/']}
SAFE_STRINGS={'','Success','Accepted','Bad request','Forbidden','Unprocessable Entity','Too Many Requests','Server error',
 'InvalidRequest','InvalidKey','InvalidUrl','InvalidHost','KeyNotFound','KeyValidationFailed','TooManyRequests','ServerError','UnprocessableEntity',
 'Invalid request','Invalid key','Invalid URL','Invalid host','Key not found','Key validation failed',
 '전송이 성공하였습니다.','URL 정보가 수신되었습니다. key 정보를 확인 중입니다.','잘못된 형식으로 요청되었습니다.','key가 유효하지 않습니다.','URL이 key 정보와 일치하지 않습니다.','과도하게 많은 요청을 보내고 있습니다.','서버 에러입니다.'}
SAFE_FIELDS={'error','message','code','status','detail'}
STATUS_CODES={200,202,400,403,422,429,500}
def require(value,code):
 if not value:raise ValueError(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def save_new(path,raw):
 require(not path.is_symlink()and not path.exists(),'observation_output_exists')
 with path.open('xb')as f:f.write(raw)
 require(path.read_bytes()==raw,'observation_readback_mismatch')
def save_json(path,value):save_new(path,(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8'))
def begin():
 root=ROOT.absolute()
 for p in [root,*root.parents]:require(not p.is_symlink(),'observation_symlink_forbidden')
 root.mkdir(exist_ok=True)
 existing=sorted(root.iterdir())
 require(len(existing)<3 and all(p.is_dir()and not p.is_symlink()and p.name==f'attempt-{i:03d}'for i,p in enumerate(existing,1)),'observation_attempt_layout')
 folder=root/f'attempt-{len(existing)+1:03d}';folder.mkdir(exist_ok=False);return folder

def safe_value(value,depth=0):
 if depth>3:return False
 if value is None:return True
 if type(value)is int:return value in STATUS_CODES
 if type(value)is str:return value in SAFE_STRINGS
 if type(value)is dict:return 0<len(value)<=5 and set(value)<=SAFE_FIELDS and all(safe_value(v,depth+1)for v in value.values())
 return False

def classify(raw):
 try:text=raw.decode('utf-8');utf8=True
 except UnicodeDecodeError:return dict(utf8=False,retainRaw=False,reason='non_utf8_body_withheld')
 if len(raw)>CAPTURE_LIMIT:return dict(utf8=utf8,retainRaw=False,reason='body_over_capture_limit_withheld')
 if text.strip()in SAFE_STRINGS:return dict(utf8=utf8,retainRaw=True,reason='fixed_public_diagnostic_vocabulary')
 def unique(pairs):
  result={}
  for key,value in pairs:
   if key in result:raise ValueError('duplicate_key')
   result[key]=value
  return result
 try:value=json.loads(text,object_pairs_hook=unique)
 except (ValueError,TypeError):return dict(utf8=utf8,retainRaw=False,reason='unrecognized_body_withheld')
 return dict(utf8=utf8,retainRaw=safe_value(value),reason='fixed_public_diagnostic_vocabulary'if safe_value(value)else'unrecognized_json_values_withheld')

def framing(headers,read_length):
 value=headers.get('content-length');declared=None;state='absent';error=None
 if value is not None:
  stripped=value.strip()
  if len(stripped)<=20 and re.fullmatch('[0-9]+',stripped):
   declared=int(stripped);state='valid'
   if declared!=read_length:error='declared_content_length_mismatch'
  else:state='invalid_or_duplicate';error='invalid_content_length'
 if 'transfer-encoding'in headers:
  if value is not None:error='conflicting_transfer_encoding_and_length'
  elif headers['transfer-encoding'].strip().lower()!='chunked':error='unrecognized_transfer_encoding'
 return dict(declaredResponseBytes=declared,contentLengthState=state,framingError=error)

def request(method,url,payload):
 from indexnow_finalize import ENDPOINT,MAX_BYTES,NoRedirect
 require(method=='POST'and url==ENDPOINT and type(payload)is dict and payload==EXPECTED,'exact_public_post_required')
 # These are the exact bytes assigned to urllib Request.data, not a reconstructed after-the-fact payload.
 data=json.dumps(payload).encode();req=Request(url,data=data,method=method,headers={'User-Agent':'SiteFactory-IndexNow/2.0','Content-Type':'application/json; charset=utf-8','Cache-Control':'no-cache'})
 require(req.data==data and req.full_url==ENDPOINT and not req.has_header('Authorization')and not req.has_header('Cookie'),'public_request_identity')
 folder=begin();save_new(folder/'request-body.json',req.data)
 record=dict(schemaVersion=1,kind='exact_public_http_request_body_observation',method='POST',endpoint=ENDPOINT,requestBytes=len(req.data),requestSHA256=sha(req.data),requestBodyFile='request-body.json',requestUTF8=True,preparedAtUTC=now(),bodyAssignedToRequest=True,networkPacketCapture=False,requestHeadersRetained=False,responseHeadersRetained=False)
 save_json(folder/'request.json',record)
 invoked=now()
 try:
  try:response=build_opener(NoRedirect).open(req,timeout=40)
  except HTTPError as error:response=error
  with response:
   read_error=None
   try:raw=response.read(MAX_BYTES+1)
   except IncompleteRead as error:raw=error.partial;read_error='incomplete_http_read'
   headers={}
   for name,value in response.headers.items():
    name=name.lower();headers[name]=headers.get(name,'')+(', 'if name in headers else'')+value
   frame=framing(headers,len(raw));within_limit=len(raw)<=MAX_BYTES;complete=within_limit and frame['framingError']is None and read_error is None
   classification=classify(raw);retained=complete and classification['retainRaw']
   response_record=dict(schemaVersion=1,transportInvokedAtUTC=invoked,observedAtUTC=now(),httpStatus=response.code,responseBytesRead=len(raw),responseBodyComplete=complete,responseSHA256=sha(raw)if complete else None,readBytesSHA256=sha(raw),responseUTF8=classification['utf8'],captureLimitBytes=CAPTURE_LIMIT,rawRetained=retained,rawFile='response-body.bin'if retained else None,withheldReason=None if retained else classification['reason']if complete else'response_exceeds_existing_transport_limit'if not within_limit else read_error or frame['framingError'],responseHeadersRetained=False,readError=read_error,**frame)
   if retained:save_new(folder/'response-body.bin',raw)
   save_json(folder/'response.json',response_record)
   require(within_limit,'oversized_http_response')
   require(complete,'incomplete_http_response')
   # Preserve the existing helper's strict UTF-8 return behavior and unchanged headers for retry semantics.
   return response.code,raw.decode('utf-8'),headers
 except Exception as error:
  # No exception body, URL query, header or server-provided string reaches logs/evidence.
  kind=type(error).__name__ if type(error).__name__ in {'TimeoutError','HTTPError','URLError','UnicodeDecodeError','ValueError','OSError','FileExistsError','PermissionError'}else'OtherError'
  save_json(folder/'failure.json',dict(schemaVersion=1,transportInvokedAtUTC=invoked,observedAtUTC=now(),state='outcome_uncertain_or_observation_failed',errorType=kind,automaticRetryAdded=False))
  raise
