import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests
import yaml
from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({'TESTING':True,'SECRET_KEY':'test-only','DATABASE':str(tmp_path/'test.db'),'TMDB_TOKEN':''})


def token(client):
    return client.get('/api/csrf').json['csrf_token']


def mutate(client, path, method='POST', **kwargs):
    return client.open(path, method=method, headers={'X-CSRF-Token':token(client)}, **kwargs)


def account(app, name='klant', admin=False):
    c=app.test_client()
    mutate(c,'/register',data={'username':name,'password':'Testpass123!','confirm_password':'Testpass123!'})
    if admin:
        with sqlite3.connect(app.config['DATABASE']) as db:
            db.execute("UPDATE users SET role='admin' WHERE username=?",(name,))
    r=mutate(c,'/login',data={'username':name,'password':'Testpass123!'})
    assert r.status_code==302
    return c


def test_registration_login_logout_and_hash(app):
    c=account(app)
    assert c.get('/videotheek').status_code==200
    with sqlite3.connect(app.config['DATABASE']) as db:
        hashed=db.execute('SELECT password_hash FROM users').fetchone()[0]
        assert hashed!='Testpass123!'
        assert hashed.startswith('scrypt:')
    mutate(c,'/logout')
    assert c.get('/videotheek').status_code==302
    assert c.get('/api/films').status_code==401


@pytest.mark.parametrize('name,password,confirm',[
    ('ab','12345678','12345678'),('valid','short','short'),
    ('valid','12345678','different'),("bad' OR 1=1",'12345678','12345678')])
def test_invalid_registration(app,name,password,confirm):
    c=app.test_client()
    r=mutate(c,'/register',data={'username':name,'password':password,'confirm_password':confirm})
    assert r.status_code==200
    with sqlite3.connect(app.config['DATABASE']) as db:
        assert db.execute('SELECT count(*) FROM users').fetchone()[0]==0


def test_duplicate_case_insensitive_and_wrong_password(app):
    c=account(app)
    r=mutate(c,'/register',data={'username':'KLANT','password':'Testpass123!','confirm_password':'Testpass123!'})
    assert b'bestaat al' in r.data
    mutate(c,'/logout')
    r=mutate(c,'/login',data={'username':'klant','password':'wrong'})
    assert b'onjuist' in r.data
    assert c.get('/api/films').status_code==401


def test_csrf_enforced(app):
    c=account(app)
    assert c.post('/api/films/1/lenen').status_code==400
    assert c.get('/logout').status_code==405
    assert c.post('/logout',data={'csrf_token':'bad'}).status_code==400


@pytest.mark.parametrize('path',['/videotheek','/geschiedenis','/admin'])
def test_protected_pages(app,path):
    assert app.test_client().get(path).status_code==302


def test_loan_return_and_audit(app):
    c=account(app)
    assert mutate(c,'/api/films/1/lenen').json['status']=='uitgeleend'
    assert mutate(c,'/api/films/1/lenen').status_code==409
    assert mutate(c,'/api/films/1/reserveren').status_code==409
    assert mutate(c,'/api/films/1/terugbrengen').json['status']=='beschikbaar'
    assert mutate(c,'/api/films/1/terugbrengen').status_code==409
    logs=c.get('/api/logs').json
    assert [l['action'] for l in logs]==['terugbrengen','huren']
    assert all(l['username']=='klant' and l['timestamp'].endswith('Z') for l in logs)


def test_reservation_cannot_be_loaned_even_by_owner(app):
    c=account(app)
    assert mutate(c,'/api/films/1/reserveren').json['status']=='gereserveerd'
    assert mutate(c,'/api/films/1/lenen').status_code==409
    assert mutate(c,'/api/films/1/annuleren').json['status']=='beschikbaar'
    assert mutate(c,'/api/films/1/lenen').status_code==200
    assert len(c.get('/api/logs').json)==3


def test_other_user_cannot_return_or_cancel_and_logs_private(app):
    a,b=account(app,'alice'),account(app,'bob')
    mutate(a,'/api/films/1/lenen')
    mutate(a,'/api/films/2/reserveren')
    assert mutate(b,'/api/films/1/terugbrengen').status_code==403
    assert mutate(b,'/api/films/2/annuleren').status_code==403
    assert b.get('/api/logs').json==[]
    film=b.get('/api/films/1').json
    assert not film['mine'] and 'holder_id' not in film
    admin=account(app,'beheer',True)
    assert len(admin.get('/api/logs').json)==2
    assert mutate(admin,'/api/films/1/terugbrengen').status_code==200
    assert admin.get('/api/logs').json[0]['username']=='beheer'


def test_crud_roles_soft_delete_retains_history(app):
    c=account(app)
    assert c.get('/admin').status_code==403
    for method,path,data in [('POST','/api/films',{'title':'X'}),('PATCH','/api/films/1',{'title':'X'}),('DELETE','/api/films/1',{})]:
        assert mutate(c,path,method,json=data).status_code==403
    a=account(app,'beheer',True)
    r=mutate(a,'/api/films',json={'title':'Nieuw','genre':'Drama','year':2024})
    assert r.status_code==201
    id=r.json['id']
    assert a.get(r.headers['Location']).json['title']=='Nieuw'
    assert mutate(a,f'/api/films/{id}','PATCH',json={'title':'Bewerkt'}).json['title']=='Bewerkt'
    mutate(c,f'/api/films/{id}/lenen')
    assert mutate(a,f'/api/films/{id}','DELETE').status_code==409
    mutate(c,f'/api/films/{id}/terugbrengen')
    assert mutate(a,f'/api/films/{id}','DELETE').status_code==204
    assert a.get(f'/api/films/{id}').status_code==404
    assert len([l for l in a.get('/api/logs').json if l['film_id']==id])==2


@pytest.mark.parametrize('payload',[{}, {'title':''},{'title':'x'*151},{'title':'x','status':'uitgeleend'}, {'title':'x','year':True},{'title':'x','tmdb_id':-1},{'title':'x','year':'2020'}])
def test_film_validation(app,payload):
    a=account(app,'beheer',True)
    assert mutate(a,'/api/films',json=payload).status_code==400


def test_filter_missing_invalid_json_and_status(app):
    c=account(app)
    assert len(c.get('/api/films?q=matrix').json)==1
    mutate(c,'/api/films/1/lenen')
    assert len(c.get('/api/films?status=uitgeleend').json)==1
    assert c.get('/api/films?status=bad').status_code==400
    assert c.get('/api/films/999').status_code==404
    assert mutate(c,'/api/films/999/lenen').status_code==404
    assert mutate(c,'/api/films/1/nonsense').status_code==404
    a=account(app,'beheer',True)
    assert mutate(a,'/api/films',data='x',content_type='text/plain').status_code==400
    assert mutate(a,'/api/films/1','PATCH',json={}).status_code==400


def test_tmdb_missing_token_success_and_failure(app):
    a=account(app,'beheer',True)
    assert mutate(a,'/api/films/1/tmdb').status_code==503
    app.config['TMDB_TOKEN']='test-token'
    response=Mock()
    response.json.return_value={'overview':'Omschrijving uit TMDB','poster_path':'/abc.jpg'}
    with patch('app.requests.get',return_value=response) as get:
        r=mutate(a,'/api/films/1/tmdb')
        assert r.status_code==200 and r.json['poster_url'].endswith('/abc.jpg')
        assert get.call_args.kwargs['timeout']==8
        assert get.call_args.kwargs['headers']['Authorization']=='Bearer test-token'
    with patch('app.requests.get',side_effect=requests.Timeout):
        assert mutate(a,'/api/films/1/tmdb').status_code==502
    assert a.get('/api/films/1').json['description']=='Omschrijving uit TMDB'
    response.json.return_value={'overview':'','poster_path':None}
    with patch('app.requests.get',return_value=response):
        assert mutate(a,'/api/films/1/tmdb').status_code==502
    mutate(a,'/api/films/1','PATCH',json={'tmdb_id':None})
    assert mutate(a,'/api/films/1/tmdb').status_code==400


def test_concurrent_borrow_only_one_winner(app):
    a,b=account(app,'alice'),account(app,'bob')
    tokens=[token(a),token(b)]
    def borrow(pair):
        c,t=pair
        return c.post('/api/films/1/lenen',headers={'X-CSRF-Token':t}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(borrow,zip([a,b],tokens)))
    assert sorted(results)==[200,409]
    with sqlite3.connect(app.config['DATABASE']) as db:
        assert db.execute('SELECT count(*) FROM logging').fetchone()[0]==1


def test_restarting_does_not_duplicate_or_reseed(app):
    a=account(app,'beheer',True)
    for f in a.get('/api/films').json:mutate(a,f'/api/films/{f["id"]}','DELETE')
    restarted=create_app(dict(app.config))
    c=restarted.test_client()
    mutate(c,'/login',data={'username':'beheer','password':'Testpass123!'})
    assert c.get('/api/films').json==[]


def test_swagger_and_templates(app):
    spec=yaml.safe_load((Path(__file__).parents[1]/'swagger.yaml').read_text())
    assert spec['openapi']=='3.0.3'
    assert all('/api/films/{film_id}/'+x in spec['paths'] for x in ('lenen','terugbrengen','reserveren','annuleren','tmdb'))
    c=account(app,'beheer',True)
    for path in ['/','/videotheek','/geschiedenis','/admin','/opdracht','/api/docs','/swagger.yaml']:
        assert c.get(path).status_code==200


def test_admin_cli_and_registration_does_not_escalate(app):
    runner=app.test_cli_runner()
    r=runner.invoke(args=['create-admin','--username','beheer','--password','Securepass123!'])
    assert r.exit_code==0
    assert runner.invoke(args=['create-admin','--username','beheer','--password','Securepass123!']).exit_code!=0
    c=app.test_client()
    mutate(c,'/register',data={'username':'hacker','password':'Testpass123!','confirm_password':'Testpass123!','role':'admin'})
    with sqlite3.connect(app.config['DATABASE']) as db:
        assert db.execute("SELECT role FROM users WHERE username='hacker'").fetchone()[0]=='gebruiker'
