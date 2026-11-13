"""Read-only control-plane diagnosis after inactive upload; never activates."""
import json
import enable_guard as g
PRIOR='54478f7d-8dd3-437b-9f0a-ad92864e9152'
CANDIDATE='8e38b102-c4a6-4321-befb-fae7b275c942'
SOURCE='49c9926ef6761442431ca15627ca2c560eacb3e5'

def flag(bindings):
    return next((b[2] for b in bindings if b[:2]==['plain_text','TELEGRAM_ORDER_ENABLED']),'absent')

def inspect():
    live=g.snapshot()
    prefix='/accounts/'+g.ACCOUNT+'/workers/scripts/'+g.WORKER+'/versions/'
    old=g.get(prefix+PRIOR);new=g.get(prefix+CANDIDATE)
    assert old.get('id')==PRIOR and new.get('id')==CANDIDATE,'Version identity mismatch'
    ob=g.normalize(old['resources']['bindings']);nb=g.normalize(new['resources']['bindings'])
    return {
        'active_version':live['version'], 'prior_still_active':live['version']==PRIOR,
        'candidate_version':CANDIDATE, 'candidate_source_matches':new.get('annotations',{}).get('workers/tag')==SOURCE,
        'candidate_only_expected_flag_delta':nb==g.enabled_bindings({'bindings':ob}),
        'prior_flag':flag(ob),'candidate_flag':flag(nb),'script_settings_flag':flag(live['bindings']),
        'script_settings_match_prior':live['bindings']==ob,'script_settings_match_candidate':live['bindings']==nb,
        'prior_recipient_present':['secret_text','TELEGRAM_ORDER_CHAT_ID'] in ob,
        'candidate_recipient_present':['secret_text','TELEGRAM_ORDER_CHAT_ID'] in nb,
        'scope_constraints':'verified by snapshot', 'public_http_requests':0,'writes':0
    }

if __name__=='__main__':
    try:print(json.dumps(inspect(),sort_keys=True))
    except Exception as exc:
        print(json.dumps({'error':str(exc) if isinstance(exc,AssertionError) else type(exc).__name__}))
        raise SystemExit(1)
