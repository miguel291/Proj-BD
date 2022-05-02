from flask import Flask, jsonify, request
import logging, psycopg2, time, config
import jwt
from datetime import datetime


app = Flask(__name__)

app.config['SECRET_KEY'] =  'segredo' #for encoding/decoding jwt tokens
app.config['ALGORITHM'] ='HS256' #for decoding jwt tokens

#Landing page
@app.route('/dbproj/')
def hello():
    return """

    Hello World!  <br/>
    <br/>
    Work developed by Diogo Henriques and Miguel Pedroso<br/>
    <br/>
    This project was developed for the 2021 BD course
    """

## Obtain all auctions, in JSON format
##   http://localhost:8080/dbproj/leiloes
@app.route("/dbproj/leiloes/", methods=['GET'], strict_slashes=True)               
def get_all_auctions():
    logger.info("###              DEMO: GET /dbproj/leiloes              ###");

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT numero, descricao FROM leilao WHERE ativo = True order by numero asc")
    rows = cur.fetchall()

    payload = []
    logger.debug("---- leiloes  ----")
    for row in rows:
        logger.debug(row)
        content = {'leilao id': int(row[0]), 'descricao': row[1], }
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)

## Apresenta todos os users (para debug)
##postaman -X POST http://localhost:8080/dbproj/user/list
@app.route("/dbproj/user/list", methods=['GET'], strict_slashes=True)               
def get_all_users():
    logger.info("###              DEMO: GET /dbproj/user/list              ###");

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM utilizador order by username asc")
    rows = cur.fetchall()

    payload = []
    logger.debug("---- users  ----")
    for row in rows:
        logger.debug(row)
        content = {'username': row[0], 'password': row[1]}
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)

## Apresenta tabela de licitações
##postaman -X POST http://localhost:8080/dbproj/bids
@app.route("/dbproj/bids/", methods=['GET'], strict_slashes=True)
def get_all_bids():
    logger.info("###              DEMO: GET /dbproj/bids             ###");

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM licitacao")
    rows = cur.fetchall()

    payload = []
    logger.debug("---- bids  ----")
    for row in rows:
        logger.debug(row)
        content = {'valor': row[0], 'momento': row[1],'utilizador': row[2],'leilaoId': row[3]}
        payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)

## Get auction pela keyword ou pelo ID
##postaman -X GET http://localhost:8080/dbproj/leiloes/<keyword> 
@app.route("/dbproj/leiloes/<keyword>/", methods=['GET'])                                
def get_auction(keyword):
    logger.info("###              DEMO: GET /dbproj/leiloes/<keyword>           ###")

    logger.debug(f'keyword: {keyword}')

    conn = db_connection()
    cur = conn.cursor()
    x = keyword.isnumeric()
    if(x):
        kw_num=keyword
        kw_str = ''
    else:
        kw_num=-1
        kw_str=keyword    

    
    cur.execute("SELECT numero, descricao,ean_artigo FROM leilao where ean_artigo = %s or descricao = %s order by numero asc", (kw_num,kw_str) )
   

    rows = cur.fetchall()
    payload = []
    #payload.append({'num':kw_num,'str':kw_str})
    
    if not rows:
        content = {'Erro' : "Nenhum leilao com essas carateristicas encontrado"}
        payload.append(content)
    else:
        for row in rows:
            logger.debug(row)
            content = {'id leilao': int(row[0]), 'descricao': row[1],'ean_artigo':row[2]}
            payload.append(content) # appending to the payload to be returned

    #content = {'leilao id': int(row[0]), 'descricao': row[1]}

    conn.close ()
    return jsonify(payload)

## Add a new user in a JSON payload
## Adicionar user
##postaman -X POST http://localhost:8080/dbproj/user/add -H "Content-Type: application/json" -d '{"username": "username", "password": "password"}'
@app.route("/dbproj/user/add", methods=['POST'])                                     
def add_user():
    logger.info("###              DEMO: POST /dbproj/user              ###");
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    logger.info("---- new username  ----")
    #logger.debug(f'payload: {payload}')

    # parameterized queries, good for security and performance
    statement = """
                  INSERT INTO utilizador (username, password)
                          VALUES ( %s,   %s )"""

    values = (payload["username"], payload["password"])

    try:
        cur.execute(statement, values)
        cur.execute("commit")
        result = {'userId': payload["username"],'ADDED?':'yes'}
    

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = 'Failed!'
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

## Termina leilões cuja data de fim já passou
##postaman -X GET http://localhost:8080/dbproj/ender
@app.route("/dbproj/ender/", methods=['GET'], strict_slashes=True)     
def ender():
    logger.info("###              DEMO: GET /dbproj/ender              ###")

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("UPDATE leilao SET ativo = FALSE WHERE ativo = TRUE and momento_fim < CURRENT_TIMESTAMP")
    cur.execute("commit")
    #query funciona e depois enviar notificaçao a todos
    payload = []
    logger.debug("---- leilao ender  ----")
    content = {'leiloes ativos atualizados com sucesso': "" }
    payload.append(content) # appending to the payload to be returned

    conn.close()
    return jsonify(payload)

## Apresenta todos os leiloes nos quais o utilizador licitou
##postaman -X GET http://localhost:8080/dbproj/leiloes/userleilao/<token de autenticação>
@app.route("/dbproj/leiloes/userleilao/<token>", methods=['GET'])
def get_auction_of_user(token):
    
    
    logger.info("###              DEMO: GET /dbproj/leiloes/<token>       ###")
    
    try:
        data = jwt.decode(token,app.config['SECRET_KEY'],app.config['ALGORITHM'])
    except:
        return jsonify({'message':'Token invalido'}),403

    
    logger.debug(f'username: {data}')

    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT numero, titulo, descricao FROM leilao where utilizador_username = %s UNION SELECT distinct numero,titulo,descricao from leilao where numero IN (select distinct leilao_numero from licitacao where utilizador_username = %s)", (data['username'],data['username']) )
    rows = cur.fetchall()       #check query
    payload = []
    if not rows:
        content = {'Utilizador sem atividade em nenhum leilao': ""}
        payload.append(content)
    else:
        for row in rows:
            logger.debug(row)
            content = {'leilao id': int(row[0]), 'titulo': row[1], 'descricao': row[2]}
            payload.append(content) # appending to the payload to be returned


    conn.close ()
    return jsonify(payload)

## Adiciona leilão caracteristicas passadas por json no postman
##postaman -X POST,GET http://localhost:8080/leilao -H "Content-Type: application/json" -d '{"ean_artigo": "ean_artigo", "preco_minimo": "preco_minimo","momento_fim":"2021-05-30 19:30","titulo" : "teste","descricao" : "testando alterecao d1riedades ","username":"Bertha Feldt" }'
@app.route("/dbproj/leilao/", methods=['POST','GET']) 
def add_auction():
    logger.info("###              DEMO: POST /dbproj/leilao              ###")
    payload = request.get_json()

    conn = db_connection()
    cur = conn.cursor()
    if "ean_artigo" not in payload or "preco_minimo" not in payload or "momento_fim" not in payload or "titulo" not in payload or "descricao" not in payload or "token" not in payload:
        return 'ean_artigo, preco_minimo,momento_fim,titulo,descricao and token needed to create new leilao\n'

    token = payload["token"]

    try:
        data = jwt.decode(token,app.config['SECRET_KEY'],app.config['ALGORITHM'])
    except:
        return jsonify({'message':'Token invalido'}),403

    username = data["username"]
    logger.info("---- new auction  ----")          
    logger.debug(f'payload: {payload}')

    statement = """
                  INSERT INTO leilao (ean_artigo,preco_minimo,momento_fim,titulo,descricao,utilizador_username)
                          VALUES (%s,%s,%s,%s,%s,%s)"""

    values = (payload["ean_artigo"], payload["preco_minimo"],payload["momento_fim"],payload["titulo"],payload["descricao"],data["username"])

    try:
        cur.execute(statement, values)
        cur.execute("commit")
        result = {'leilaoId': payload["ean_artigo"]}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = 'Failed!'
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

## Faz login do utilizador, recebe um json com username e password do utilizador 
##curl -X PUT http://localhost:8080/dbproj/user -H "Content-Type: application/json" -d '{"username": "Pearle Toomey", "password": "password"}'
@app.route("/dbproj/user", methods=['PUT','GET'])
def loggin_user():
    logger.info("###              DEMO: PUT /dbproj/user              ###")
    content = request.get_json()

    conn = db_connection()
    cur = conn.cursor()

    if "username" not in content or "password" not in content:                  #falta token para devolver
       return 'username and password are required to login\n'

    logger.info("---- login user ----")
    logger.debug(f'payload: {content}')
    # parameterized queries, good for security and performance
    statement = """
                  SELECT username, password FROM utilizador
                          WHERE USERNAME = %s and PASSWORD = %s"""

    values = (content['username'],content['password'])
    cur.execute(statement,values)
    row = cur.fetchall()
    payload = []
    if not row :
        content = {'erro': "User or password wrong"}
        payload.append(content)
    else:
        
        authToken = jwt.encode({'username': content['username'],'password':content['password']},app.config['SECRET_KEY'])
        payload.append(authToken) # appending to the payload to be returned the token
        payload.append("GUARDAR ESTE TOKEN PARA OPERACOES FUTURAS")
    conn.close()
    return jsonify(payload)

#Faz um licitação passar token de autenticação pelo body do postman e id do leilao e valor de licitação pelo URL
#"Content-Type: application/json" -d '{"token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6Ik1pa2tpIEx1ZWR0a2UiLCJwYXNzd29yZCI6InBhc3N3b3JkIn0.KKtlHh1DE7OPxPu95jOFY_QkoG1O46pYw1Jiz3rLBVU""}'
@app.route("/dbproj/licitar/<leilaoId>/<licitacao>/", methods=['GET'])
def licita(leilaoId,licitacao):
    logger.info("###              DEMO: GET /dbproj/licitar/<leilaoId>/<licitacao>          ###")
    payload = request.get_json()

    token = payload['token']
    
    try:
        data = jwt.decode(token,app.config['SECRET_KEY'],app.config['ALGORITHM'])
        logger.debug(f"token {data}")
    except:
        return jsonify({'message':'Token invalido'}),403
    
    conn = db_connection()
    cur = conn.cursor()
    logger.info("---- new bid  ----")                                
    cur.execute("UPDATE leilao SET ativo = FALSE WHERE ativo = TRUE and momento_fim < CURRENT_TIMESTAMP")
    cur.execute("commit")
    statement = """
                   SELECT licitar(%s,%s,%s)"""

    values = (data['username'],licitacao,leilaoId)

    try:
        cur.execute(statement, values)
        row = cur.fetchall()
        cur.execute("commit")
        
        result = {'Result': row}
        #result = {'leilaoId': leilaoId, 'licitacao': licitacao}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = 'Failed!'
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

#Apresenta todas as caracteristicas de um certo leilão, deve ser passado o ID do leilão pelo URL
#GET http://localhost:8080/dbproj/leilao/<ID do leilao que quer consultar>
@app.route("/dbproj/leilao/<leilaoId>", methods=['GET'])
def auction_details(leilaoId):
        logger.info("###              DEMO: PUT /dbproj/leilao/{leilaoId}              ###");
        
        conn = db_connection()
        cur = conn.cursor()
        payload=[]
        logger.info("---- change auction properties ----")
        statement ="""
                    SELECT * FROM leilao WHERE numero=%s"""


        values = (leilaoId)

        try:
            cur.execute(statement, values)
            rows = cur.fetchall()
            for row in rows:
                content={'id':row[0],'ean_artigo':row[1],'preco_minimo':row[2],'preco_vencedor':row[3],'momento_fim':row[4],'ativo':row[5],'titulo':row[6],'descricao':row[7],'username do criador': row[8]}
                payload.append(content)
          
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(error)
            payload.append('Failed!')
        finally:
            if conn is not None:
                conn.close()
        return jsonify(payload)

#Altera titulo e/ou descrição de um certo leilão, passar json pelo postman com novo titulo e descrição se desejar só alterar um dos parametros deve colocar "" no outro
#PUT  http://localhost:8080/dbproj/leilao/change/<ID do leilao que quer alterar>
#"Content-Type: application/json" -d {"newDescricao":"Introduzir a descrição nova","newTitulo":"Introduzir o novo titulo"}
@app.route("/dbproj/leilao/change/<leilaoId>", methods=['PUT'])
def auction_change_details(leilaoId): #a funcionar
    logger.info("###              DEMO: PUT /dbproj/leilao/{leilaoId}              ###");    
    conn = db_connection()
    cur = conn.cursor()
    payload=[]
    payload= request.get_json()

    
    if payload['newTitulo'] == "" and payload['newDescricao'] != "":
        statement=""" call newDescricao(%s,%s)
                        """
        values=(payload['newDescricao'],leilaoId)
     

    elif payload['newDescricao'] == "" and payload['newTitulo'] != "":
        statement=""" call newTitulo(%s,%s)
                        """
        values=(payload['newTitulo'],leilaoId)
     
    elif payload['newDescricao'] != "" and payload['newTitulo'] != "":
        statement=""" call newTitulo(%s,%s);
        call newDescricao(%s,%s)
                        """
        values=(payload['newTitulo'],leilaoId,payload['newDescricao'],leilaoId)
    else:
        return"""PAYLOAD ENVIADO ERRADO"""

    try:
        cur.execute(statement, values)
        cur.execute("commit")
        result={'Success:': 'yes', 'newTitulo':payload['newTitulo'],'newDescricao':payload['newDescricao'],'id_leilao': leilaoId}
            
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = 'Failed!'
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)
##########################################################
## DATABASE ACCESS
##########################################################

def db_connection():
    db = psycopg2.connect(user = config.user,
                            password = config.password,
                            host = config.host,
                            port = config.port,
                            database = config.database)
    return db

#Consulta mensagens referentes a um certo utilizador
#Passar token de autenticação do utilizador em questão pelo URL
#http://localhost:8080/dbproj/mensagens/<Token do Utilizador que pretende consultar mensagem>
@app.route("/dbproj/mensagens/<token>", methods=['GET'], strict_slashes=True)
def get_user_messages(token):
    logger.info("###              DEMO: GET /dbproj/mensagens/<token>             ###");

    conn = db_connection()
    cur = conn.cursor()

    try:
        data = jwt.decode(token,app.config['SECRET_KEY'],app.config['ALGORITHM'])
    except:
        return jsonify({'message':'Token invalido'}),403

    cur.execute("select texto,momento,utilizador_username,leilao_numero from mensagem where leilao_numero in (select distinct leilao_numero from licitacao where utilizador_username = %s) and publi = true or leilao_numero in (select distinct leilao_numero from licitacao where utilizador_username = %s) and utilizador_username = %s UNION select texto,momento,utilizador_username,leilao_numero from mensagem where leilao_numero in (select distinct numero from leilao where utilizador_username = %s) UNION select texto,momento,utilizador_username,leilao_numero from mensagem where leilao_numero in (select distinct leilao_numero from mensagem where utilizador_username = %s) and publi = true order by momento asc",(data['username'],data['username'],data['username'],data['username'],data['username']))
    rows = cur.fetchall()
    payload=[]
    if not rows:
        content = {'Utilizador sem mensagens': ""}
        payload.append(content)
    else:
        for row in rows:
            logger.debug(row)
            content = {'texto mensagem': row[0], 'momento': row[1], 'user': row[2],'idLeilao':row[3]}
            payload.append(content) # appending to the payload to be returned


    conn.close ()
    return jsonify(payload)

#User publica mensagem no leilao
#Passar por json no postman o token de autenticação de quem vai escreve a mensagem, a mensagem e o Id do leilão 
#curl -X POST http://localhost:8080/dbproj/insert/mensagem/ -H "Content-Type: application/json" -d '{"mensagem": "teste", "token": "username", "leilaoId": "25"}'
@app.route("/dbproj/insert/mensagem/", methods=['POST'])                
def insert_message():
    logger.info("###              DEMO: GET /dbproj/mensagens/          ###")

    conn = db_connection()
    cur = conn.cursor()
    payload = request.get_json()

    if "mensagem" not in payload or "token" not in payload or "leilaoId" not in payload:
        return "mensagem,token and leilaoId needed to add new message\n"

    try:
        data = jwt.decode(payload['token'],app.config['SECRET_KEY'],app.config['ALGORITHM'])
    except:
        return jsonify({'message':'Token invalido'}),403

    statement = """
                  INSERT INTO mensagem (texto, momento,publi, utilizador_username,leilao_numero)
                    VALUES (%s,CURRENT_TIMESTAMP,TRUE,%s,%s)"""

    values = (payload["mensagem"], data["username"],payload["leilaoId"])

    try:
        cur.execute(statement, values)
        cur.execute("commit")
        result = {'mensagem': payload["mensagem"],'leilao': payload["leilaoId"]}

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        result = 'Failed!'
    finally:
        if conn is not None:
            conn.close()

    return jsonify(result)

##########################################################
## MAIN
##########################################################
if __name__ == "__main__":

    # Set up the logging
    logging.basicConfig(filename="logs/log_file.log")
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s',
                              '%H:%M:%S')
                              # "%Y-%m-%d %H:%M:%S") # not using DATE to simplify
    ch.setFormatter(formatter)
    logger.addHandler(ch)


    time.sleep(1) # just to let the DB start before this print :-)


    logger.info("\n---------------------------------------------------------------\n" +
                  "API v1.0 online: http://localhost:8080/dbproj\n\n")




    app.run(host="0.0.0.0", debug=True)
