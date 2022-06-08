from ast import Try
from asyncio.windows_events import NULL
from contextlib import redirect_stderr
from distutils.log import debug
from email import message
from msilib.schema import Error
from operator import methodcaller
import os, datetime
from pickle import NONE
from sys import path
from time import time
from click import confirm, echo
from flask import Flask, render_template, render_template_string, request, redirect, flash, url_for, session
from werkzeug.utils import secure_filename
from datetime import timedelta
import matplotlib.pyplot as plt

import matplotlib
matplotlib.use('agg')
plt.rc('ytick', labelsize=16)   
plt.rc('xtick', labelsize=12)  

import psycopg2, numpy as np

from psycopg2 import OperationalError

app = Flask(__name__)
app.secret_key = b'secret'
app.permanent_session_lifetime = timedelta(minutes=5)


BASE_PATH =  'uploads'
ALLOWED_EXT = {'txt'}
conf = 0

r1 = ''
r2 = ''
r3 = ''
r4 = ''
r5 = ''
r6 = ''
r7 = ''
r8 = ''

_email = ''
_username = ''

def create_connection():
    connection = None
    try:
        connection = psycopg2.connect(
            database="collectpedia2",
            user="postgres",
            password="fkv2arh",
            host="127.0.0.1",
            port="5432",
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection


def selecao(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except OperationalError as e:
        print(f"The error '{e}' occurred")

def execute_query (connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query executed successfully")
    except OperationalError as e:
        print(f"The error '{e}' occurred")

connection = create_connection()

@app.route('/logar', methods=['POST'])
def logar():

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        vet_e_s = senha, email
        
        consulta =( f'''
                        SELECT	C.email, C.senha, C.username
                        FROM	colecionador C
                        WHERE	C.senha like '{vet_e_s[0]}'  
                        AND C.email like '{vet_e_s[1]}' ''' )
        temp = []
        temp = selecao(connection, consulta)
        if temp:
            global _email 
            _email = vet_e_s[1]
            global _username
            _username = temp[0][2]

            session.permanent = True
            session["email"] = email
            session["senha"] = senha

            return redirect(url_for('user', r1=0, r2 =0, r3=0, r4=0, r5=0, r6 =0, r7=0, r8=0))
        
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop("email", None)
    session.pop("senha", None)
    return redirect(url_for('login'))

@app.route('/cadastrar', methods=['POST'])
def cadastrar():

    if request.method == 'POST':
        usern = request.form['usern']
        email = request.form['email']
        senha = request.form['senha']
        conf_s = request.form['conf_s']

        if conf_s != senha:
            flash("Senhas não combinam. Digite-as novamente.")
        else:

            user_q = (

                f'''
                SELECT	C.username
                FROM	colecionador C
                WHERE	C.username like '{usern}'
                '''
            )
            result = []
            try:
                result1 = selecao(connection, user_q)
            except OperationalError as e:
                echo(f"O erro {e} ocorreu. Tente novamente.")
            if result1:
                echo("Username já existe. Escolha outro.")
            else:
                email_q = (

                    f'''
                        SELECT	C.email
                        FROM	colecionador C
                        WHERE	C.email like '{email}'
                    '''
                )
                result2 = []
                try:
                    result2 = selecao(connection, email_q)
                except OperationalError as e:
                    echo(f"O erro {e} ocorreu. Tente novamente.")
                if result2:
                    echo("E-mail já cadastrado. Escolha outro.")
                else:
                    echo('Deu certo!!')
                    
                    cadastro_q = (
                        f'''
                        INSERT INTO colecionador 
                        VALUES ('{usern}', '{email}', '{senha}')
                        '''
                    )

                    try:
                        execute_query(connection, cadastro_q)
                    except OperationalError as e:
                        echo(f"O erro {e} ocorreu. Tente novamente.")

                    return redirect(url_for('layouts'))
    return redirect(url_for('signup'))


@app.route('/', methods=['GET', 'POST'])
def layouts():

    consulta = (
        f'''
            SELECT		E.foto_de_capa as capa, E.fk_serie_nome_intern as nome, E.fk_serie_ciclo_de_num as vol, E.numero as num, MAX(E.data_lanc) as top_recentes
            FROM		edicao E
            GROUP BY	nome, vol, num, capa
            ORDER BY 	top_recentes DESC, nome ASC, vol ASC, num ASC
        '''
    )

    result = []
    try:
        result = selecao(connection, consulta)
    except OperationalError as e:
        echo(f"O erro {e} ocorreu. Tente novamente.")

    v1 = result[0][0]
    v2 = result[1][0]
    v3 = result[2][0]
    v4 = result[3][0]

    return render_template('index.html', c1=v1, c2=v2, c3=v3, c4=v4)


@app.route('/buscar', methods=['POST'])
def buscar():

    if request.method == 'POST':

        busca = request.form["home-busca"]
        tipo_busca = request.form["opc-busca"]
        
        if tipo_busca == "Comics":
            consulta = (
                f'''
                
                (	SELECT 	E.fk_serie_nome_intern as NOME, E.fk_serie_ciclo_de_num AS VOL , COUNT(E.fk_serie_nome_intern) as NUM_EDICOES, tab_ano.ano_pub AS ANO_PUB, P.fk_editora_nome AS EDITORA
                FROM	serie S, publica P, (SELECT EXTRACT (YEAR FROM E.data_lanc) as ano_pub, E.fk_serie_nome_intern, E.fk_serie_ciclo_de_num
                                                        FROM edicao E
                                                        WHERE E.numero = '1A' AND E.fk_serie_nome_intern iLIKE '%{busca}%'
                                                        ORDER BY E.fk_serie_nome_intern, E.fk_serie_ciclo_de_num) tab_ano NATURAL JOIN edicao E

                WHERE	(E.fk_serie_nome_intern, E.fk_serie_ciclo_de_Num) = (nome_intern, ciclo_de_num) AND
                        (P.fk_serie_nome_intern, P.fk_serie_ciclo_de_Num) = (nome_intern, ciclo_de_num)

                GROUP BY NOME, VOL, ANO_PUB, EDITORA)
                
            EXCEPT
                
                (SELECT 	M.fk_serie_nome_intern as NOME, M.fk_serie_ciclo_de_num as vol, COUNT(E.fk_serie_nome_intern) as NUM_TANKOS, 
                        tab_ano.ano_pub AS ANO_PUB, P.fk_editora_nome AS EDITORA
                FROM	serie S, publica P, manga M, (SELECT EXTRACT (YEAR FROM E.data_lanc) as ano_pub, E.fk_serie_nome_intern, E.fk_serie_ciclo_de_num
                                                        FROM 	edicao E
                                                        WHERE 	E.numero = '1A' AND
                                                                E.fk_serie_nome_intern iLIKE '%{busca}%'
                                                        ORDER BY E.fk_serie_nome_intern, E.fk_serie_ciclo_de_num) tab_ano NATURAL JOIN edicao E

                WHERE	(E.fk_serie_nome_intern, E.fk_serie_ciclo_de_Num) = (nome_intern, ciclo_de_num) AND
                        (P.fk_serie_nome_intern, P.fk_serie_ciclo_de_Num) = (nome_intern, ciclo_de_num) AND
                        (M.fk_serie_nome_intern, M.fk_serie_ciclo_de_Num) = (nome_intern, ciclo_de_num) 


                GROUP BY NOME, vol, ANO_PUB, EDITORA)
                
            ORDER BY NOME ASC, VOL ASC, NUM_EDICOES ASC
                
                '''
            )
            result = []
            try:
                result = selecao(connection, consulta)
            except OperationalError as e:
                echo(f"O erro {e} ocorreu. Tente novamente.")
            return render_template('result_busca_c.html', result = result, busca = busca)
        if tipo_busca == "Manga":
            consulta = (
                f'''

                  SELECT 	M.fk_serie_nome_intern as NOME, M.nome_jap as NOME_JAP, COUNT(E.fk_serie_nome_intern) as NUM_TANKOS, 
                            tab_ano.ano_pub AS ANO_PUB, P.fk_editora_nome AS EDITORA, M.demografia as DEMOGRAFIA, M.fk_serie_ciclo_de_num as vol
                    FROM	serie S, publica P, manga M, (SELECT EXTRACT (YEAR FROM E.data_lanc) as ano_pub, E.fk_serie_nome_intern, E.fk_serie_ciclo_de_num
                                                            FROM 	edicao E
                                                            WHERE 	E.numero = '1' AND
                                                                    E.fk_serie_nome_intern iLIKE '%{busca}%'
                                                            ORDER BY E.fk_serie_nome_intern, E.fk_serie_ciclo_de_num) tab_ano NATURAL JOIN edicao E

                    WHERE	(E.fk_serie_nome_intern, E.fk_serie_ciclo_de_Num) = (nome_intern, ciclo_de_num) AND
                            (P.fk_serie_nome_intern, P.fk_serie_ciclo_de_Num) = (nome_intern, ciclo_de_num) AND
                            (M.fk_serie_nome_intern, M.fk_serie_ciclo_de_Num) = (nome_intern, ciclo_de_num) 

                    GROUP BY NOME, NOME_JAP, ANO_PUB, EDITORA, DEMOGRAFIA, vol
                    ORDER BY NOME

                '''
            )
            result = []
            try:
                result = selecao(connection, consulta)
            except OperationalError as e:
                echo(f"O erro {e} ocorreu. Tente novamente.")
            return render_template('result_busca_m.html', result = result, busca = busca)


@app.route('/add_exemplar', methods=['GET', 'POST'])
def add_exemplar():

    if "email" and "senha" in session:
        email = session["email"]
        senha = session["senha"]
    else:
        return redirect(url_for('login'))

    if request.method == 'POST':
        temp = request.form['ed_add']
        temp = str(temp)
        temp = temp.replace('+', ' ')
        temp = temp.split('_')

        consulta = (

            f'''
                SELECT  *
                FROM    colecao
                WHERE   fk_colecionador_email like '{_email}'
            '''
        )

        result = []
        try:
            result = selecao(connection, consulta)
        except OperationalError as e:
            echo(f"O erro {e} ocorreu. Tente novamente.")

    return render_template('add_exemplar.html', d_edicao = temp, colecoes = result)

@app.route('/add_at_colecao/<nome>/<vol>/<num>/<data_l>', methods=['POST', 'GET'])
def add_na_colecao(nome, vol, num, data_l):
    if request.method == 'POST':
        conserv = request.form['opc-nota']
        data_aquis = request.form['data-aq']
        opc_col = request.form['opc-col']
        nome = nome.replace('+', ' ')
        
        consulta1 = (
            f'''
            
                INSERT INTO Exemplar ( estado_conserv, fk_edicao_numero, data_aquis, fk_edicao_data_lanc, fk_edicao_nome_intern, fk_edicao_ciclo_de_num)
                VALUES
                ('{conserv}', '{num}','{data_aquis}', '{data_l}', '{nome}', {vol})
            
            
            '''

        )

        try:
            execute_query(connection, consulta1)
        except OperationalError as e:
            echo(f"O erro {e} ocorreu. Tente novamente.")

        consulta2 = (
            f'''
                SELECT	MAX(E.id)
                FROM	exemplar E
                WHERE	E.fk_edicao_nome_intern like '{nome}' AND E.fk_edicao_ciclo_de_num = {vol}
            '''
        )

        id_max = ''
        try:
            id_max = selecao(connection, consulta2)
        except OperationalError as e:
            echo(f"O erro {e} ocorreu. Tente novamente.")

        id_final = int(id_max[0][0])
        
        consulta3 = (
            f'''
                INSERT INTO Agrega
                VALUES
                ('{opc_col}', '{_email}', '{id_final}')   
            '''
        )

        try:
            execute_query(connection, consulta3)
        except OperationalError as e:
            echo(f"O erro {e} ocorreu. Tente novamente.")
        
    return redirect(url_for('layouts'))



@app.route('/adm_colecoes', methods=['GET', 'POST'])
def adm_colecoes():
    
    if "email" and "senha" in session:
        email = session["email"]
        senha = session["senha"]
    else:
        return redirect(url_for('login'))

    consulta = (
      f'''
         SELECT *
        FROM	(SELECT		A.fk_colecao_nome_colecao as nome_c, COUNT(A.fk_exemplar_id)
		FROM		agrega A JOIN exemplar E on (fk_exemplar_id = id)
		WHERE		A.fk_colecao_email like '{_email}'
		GROUP BY	nome_c) as TAB1 RIGHT JOIN 
		(SELECT		C.nome_colecao as nome_c
		FROM		colecao C
		WHERE		C.fk_colecionador_email like '{_email}'
		GROUP BY	nome_c) as TAB2 using (nome_c)
      '''
    )

    result = ''
    try:
        result = selecao(connection, consulta)
    except OperationalError as e:
        echo(f"O erro {e} ocorreu. Tente novamente.")
    
    return render_template('adm_colecoes.html', matriz = result)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if "email" and "senha" in session:
        return redirect(url_for('user', r1=0, r2 =0, r3=0, r4=0, r5=0, r6 =0, r7=0, r8=0))
    return render_template('login.html')

@app.route('/user/<r1><r2><r3><r4><r5><r6><r7><r8>', methods=['GET', 'POST'])
def user(r1, r2, r3, r4, r5, r6, r7, r8):

    consulta = (
      f'''SELECT *
            FROM	(SELECT		A.fk_colecao_nome_colecao as nome_c, COUNT(A.fk_exemplar_id), MAX(E.data_aquis)
                    FROM		agrega A JOIN exemplar E on (fk_exemplar_id = id)
                    WHERE		A.fk_colecao_email like '{_email}'
                    GROUP BY	nome_c
                    ORDER BY	nome_c) as TAB1 RIGHT JOIN 
                    (SELECT		C.nome_colecao as nome_c
                    FROM		colecao C
                    WHERE		C.fk_colecionador_email like '{_email}'
                    GROUP BY	nome_c) as TAB2 using (nome_c)
      '''
    )

    result = ''
    try:
        result = selecao(connection, consulta)
    except OperationalError as e:
        echo(f"O erro {e} ocorreu. Tente novamente.")
    
    result = list(result)
    for i in range(len(result)):
        result[i] = list(result[i])
        if result[i][1] is None:
            result[i][1] = '0'
            result[i][2] = "Sem aquisições."

    if "email" and "senha" in session:
        email = session["email"]
        senha = session["senha"]
    else:
        return redirect(url_for('login'))

    render_template('layouts.html')
    return render_template('user.html', matriz = result, r1 = r1, r2=r2, r3=r3, r4=r4, r5=r5, r6=r6, r7=r7, r8=r8)

@app.route('/serie/<editora>/<nome_s>/<vol>/<num>', methods=['GET','POST'])
def serie(nome_s, vol, num, editora):

    nome_s = str(nome_s)
    nome_s = nome_s.replace('_', ' ')

    consulta1 = (
        f'''
            SELECT	infos.fk_serie_nome_intern as nome, infos.numero as num,  infos.un_monetaria as un_mon, infos.preco as preco
            FROM	edicao infos
            WHERE	infos.fk_serie_nome_intern LIKE '{nome_s}' AND infos.fk_serie_ciclo_de_num = {vol}
            ORDER BY nome, num
        '''
    )
    result1 = []
    try:
        result1 = selecao(connection, consulta1)
    except OperationalError as e:
        echo(f"O erro {e} ocorreu. Tente novamente.")

    consulta2 = (
        f'''
           SELECT		S.nome_intern as nome, E.numero as num, S.ciclo_de_num as vol,
			E.un_monetaria as mon, E.preco as preco, E.data_lanc, C.fk_contribuidor_nome C_nome,
			C.funcao as func, S.estado_pub_atual, E.foto_de_capa as capa
            FROM		contribui C, edicao E, serie S
            WHERE		(E.fk_serie_nome_intern, E.fk_serie_ciclo_de_num) = (S.nome_intern,S.ciclo_de_Num) AND 
                        (S.nome_intern,S.ciclo_de_Num) = (C.fk_serie_nome_intern, C.fk_serie_ciclo_de_num) AND 
                        E.fk_serie_nome_intern LIKE '{nome_s}' AND S.ciclo_de_num = {vol} AND E.numero = '{num}'
            ORDER BY	nome, num
        '''
    )
    result2 = []
    try:
        result2 = selecao(connection, consulta2)
    except OperationalError as e:
        echo(f"O erro {e} ocorreu. Tente novamente.")

    return render_template('s_cadastradas.html', prem_esq = result1, prem_dir = result2, vol = vol, num = num, editora = editora)


@app.route('/manga/<demo>/<editora>/<nome_m>/<jap>/<vol>/<num>', methods=['GET','POST'])
def serie_m(nome_m, vol, num, demo, jap, editora):

    nome_m = str(nome_m)
    nome_m = nome_m.replace('_', ' ')

    consulta1 = (
        f'''
          SELECT	infos.fk_serie_nome_intern as nome, infos.numero as num, infos.un_monetaria as un_mon, infos.preco as preco
            FROM	(tankobon JOIN edicao on (fk_edicao_nome_intern, fk_edicao_numero, fk_edicao_data_lanc, fk_edicao_ciclo_de_num) = 
                    (fk_serie_nome_intern, numero, data_lanc, fk_serie_ciclo_de_num)) as infos
            WHERE	infos.fk_serie_nome_intern LIKE '{nome_m}' AND infos.fk_serie_ciclo_de_num = {vol}
            ORDER BY nome, num
        '''
    )
    result1 = []
    try:
        result1 = selecao(connection, consulta1)
    except OperationalError as e:
        echo(f"O erro {e} ocorreu. Tente novamente.")

    consulta2 = (
        f'''
          
            SELECT		S.nome_intern as nome, T.fk_edicao_numero as num, CP.num_cap as caps,
                        E.un_monetaria as mon, E.preco as preco, E.data_lanc, C.fk_contribuidor_nome mangaka,
                        C.funcao as func, S.estado_pub_atual, E.foto_de_capa as capa
            FROM		contribui C, edicao E, serie S, tankobon T, capitulo CP
            WHERE		(E.fk_serie_nome_intern, E.fk_serie_ciclo_de_num) = (S.nome_intern,S.ciclo_de_Num) AND 
                        (S.nome_intern,S.ciclo_de_Num) = (C.fk_serie_nome_intern, C.fk_serie_ciclo_de_num) AND 
                        (T.fk_edicao_numero, T.fk_edicao_data_lanc, T.fk_edicao_nome_intern, T.fk_edicao_ciclo_de_num) =
                        (E.numero, E.data_lanc, E.fk_serie_nome_intern, E.fk_serie_ciclo_de_num) AND
                        (T.fk_edicao_numero, T.fk_edicao_data_lanc, T.fk_edicao_nome_intern, T.fk_edicao_ciclo_de_num) =
                        (CP.fk_tankobon_numero, CP.fk_tankobon_data_lanc, CP.fk_tankobon_nome_intern,CP.fk_tankobon_ciclo_de_num) AND
                        E.fk_serie_nome_intern LIKE '{nome_m}' AND S.ciclo_de_num = {vol} AND E.numero = '{num}'
            ORDER BY	nome, num
        '''
    )
    result2 = []
    try:
        result2 = selecao(connection, consulta2)
    except OperationalError as e:
        echo(f"O erro {e} ocorreu. Tente novamente.")

    

    return render_template('m_cadastrados.html', prem_esq = result1, prem_dir = result2, vol = vol, num = num, demo = demo, jap = jap, editora = editora)

@app.route('/colecao/<nome>', methods=['GET','POST'])
def user_colecao(nome):

    if "email" and "senha" in session:
        email = session["email"]
        senha = session["senha"]
    else:
        return redirect(url_for('login'))

    consulta1 =(
        f''' 
            SELECT	ED.fk_serie_nome_intern as nome,  ED.fk_serie_ciclo_de_num as vol1, COUNT(*) as num
            FROM	edicao ED
            WHERE	(ED.fk_serie_nome_intern,ED.fk_serie_ciclo_de_num, ED.numero) in
                    (SELECT		E.fk_edicao_nome_intern as nome_s, E.fk_edicao_ciclo_de_num as vol, ED.numero
                    FROM		agrega A, exemplar E, edicao ED
                    WHERE		A.fk_exemplar_id = E.id AND
                                (E.fk_edicao_numero, E.fk_edicao_data_lanc, E.fk_edicao_nome_intern, E.fk_edicao_ciclo_de_num) =
                                (ED.numero, ED.data_lanc, ED.fk_serie_nome_intern, ED.fk_serie_ciclo_de_num) AND
                                A.fk_colecao_nome_colecao like '{nome}' AND
                                A.fk_colecao_email like '{_email}'
                    GROUP BY 	nome_s, vol, ED.numero)
            GROUP BY nome, vol1
            ORDER BY nome, vol1, num
        '''
    )

    res1 = []
    try:
        res1 = selecao(connection, consulta1)
    except OperationalError as e:
        echo(f"O erro {e} ocorreu. Tente novamente.")

    res2 = []
    for linhas in res1:

        consulta2 = (
            f'''
                SELECT		E.fk_edicao_nome_intern as nome, E.fk_edicao_ciclo_de_num as vol, E.fk_edicao_numero as num, E.data_aquis as dt, E.estado_conserv as e_c, E.id
                FROM		agrega A, exemplar E, edicao ED
                WHERE		fk_exemplar_id = id AND 
                            ( ED.numero, ED.data_lanc, ED.fk_serie_nome_intern,ED.fk_serie_ciclo_de_num ) =
                            (E.fk_edicao_numero, E.fk_edicao_data_lanc, E.fk_edicao_nome_intern, E.fk_edicao_ciclo_de_num) AND
                            A.fk_colecao_nome_colecao like '{nome}' AND
                            A.fk_colecao_email like '{_email}' AND
                            E.fk_edicao_nome_intern like '{linhas[0]}' AND
                            E.fk_edicao_ciclo_de_num = {linhas[1]}

                ORDER BY	nome ASC, vol ASC, num ASC , dt ASC , e_c DESC 

            '''
        )

        try:
            res2+= selecao(connection, consulta2)
        except OperationalError as e:
            echo(f"O erro {e} ocorreu. Tente novamente.")

        temp3 = []
        for linhas in res1:

            consulta3 = (
                f'''
                    
                    SELECT	ED.fk_serie_nome_intern as nome,  ED.fk_serie_ciclo_de_num as vol1, COUNT(*) as num
                    FROM	edicao ED
                    WHERE	(ED.fk_serie_nome_intern,ED.fk_serie_ciclo_de_num, ED.numero) in
                            ((SELECT		ED.fk_serie_nome_intern as nome_s,  ED.fk_serie_ciclo_de_num as vol, ED.numero as num
                            FROM		edicao ED
                            GROUP BY 	nome_s, vol, num
                            ORDER BY	nome_s, vol, num)
                            except



                            (SELECT		E.fk_edicao_nome_intern as nome_s, E.fk_edicao_ciclo_de_num as vol, ED.numero
                            FROM		agrega A, exemplar E, edicao ED
                            WHERE		A.fk_exemplar_id = E.id AND
                                        (E.fk_edicao_numero, E.fk_edicao_data_lanc, E.fk_edicao_nome_intern, E.fk_edicao_ciclo_de_num) =
                                        (ED.numero, ED.data_lanc, ED.fk_serie_nome_intern, ED.fk_serie_ciclo_de_num) AND
                                        A.fk_colecao_nome_colecao like '{nome}' AND
                                        A.fk_colecao_email like '{_email}'
                            GROUP BY 	nome_s, vol, ED.numero))
                    GROUP BY nome, vol1
                    ORDER BY nome, vol1, num

                '''
            )

            try:
                temp3+= selecao(connection, consulta3)
            except OperationalError as e:
                echo(f"O erro {e} ocorreu. Tente novamente.")
            
            res3= []
            for linhas_p in res1:
                for linhas_f in temp3:
                    if (linhas_p[0],linhas_p[1]) == (linhas_f[0],linhas_f[1]):
                        res3+=[(linhas_f[0],linhas_f[1],linhas_f[2])]
                        break
    
    return render_template('colecao.html', nome = nome, res1 = res1, res2 = res2, res3=res3, len_res1 = len(res1))    


@app.route('/exibir_info/', methods=[ 'POST'])
def exibir_info():

    if request.method == 'POST':
        nome_col = request.form['escolha']

        
        consulta1 = (
            f'''
                SELECT		A.fk_colecao_nome_colecao as nome, COUNT(DISTINCT P.fk_editora_nome) as Num_Ed_Col, COUNT(A.*) as Num_Ex_Col
                FROM		agrega A, exemplar E, edicao ED, serie S, publica P
                WHERE		A.fk_exemplar_id = E.id AND
                            (E.fk_edicao_numero, E.fk_edicao_data_lanc, E.fk_edicao_nome_intern, E.fk_edicao_ciclo_de_num) =
                            (ED.numero, ED.data_lanc, ED.fk_serie_nome_intern, ED.fk_serie_ciclo_de_num) AND
                            (ED.fk_serie_nome_intern, ED.fk_serie_ciclo_de_num) = (S.nome_intern, S.ciclo_de_num) AND
                            (P.fk_serie_ciclo_de_num, P.fk_serie_nome_intern) = (S.ciclo_de_num, S.nome_intern) AND
                            A.fk_colecao_nome_colecao like '{nome_col}' AND
                            A.fk_colecao_email like '{_email}'
                GROUP BY 	nome
            '''
        )

        consulta2 = (
            f''' 
                
                SELECT		S.estado_pub_atual as e_p, COUNT(*) as contagem
                FROM		serie S
                WHERE		(S.nome_intern, S.ciclo_de_num, S.estado_pub_atual) in
                            (SELECT		S.nome_intern, S.ciclo_de_num, S.estado_pub_atual
                            FROM		agrega A, exemplar E, edicao ED, serie S
                            WHERE		A.fk_exemplar_id = E.id AND
                                        (E.fk_edicao_numero, E.fk_edicao_data_lanc, E.fk_edicao_nome_intern, E.fk_edicao_ciclo_de_num) =
                                        (ED.numero, ED.data_lanc, ED.fk_serie_nome_intern, ED.fk_serie_ciclo_de_num) AND
                                        (ED.fk_serie_nome_intern, ED.fk_serie_ciclo_de_num) = (S.nome_intern, S.ciclo_de_num) AND
                                        A.fk_colecao_nome_colecao like '{nome_col}' AND
                                        A.fk_colecao_email like '{_email}'
                            GROUP BY 	S.estado_pub_atual, S.nome_intern, S.ciclo_de_num)
                GROUP BY	e_p
                ORDER BY	e_p, contagem
            
            
            '''
        )
        
        consulta3 = (
            f''' 
                
                SELECT		G.genero, count(*) as top_3
                FROM		genero G
                WHERE 		(G.fk_serie_nome_intern, G.fk_serie_ciclo_de_num,G.genero)IN 	
                            (SELECT		G.fk_serie_nome_intern, G.fk_serie_ciclo_de_num, G.genero
                            FROM		agrega A, exemplar E, edicao ED, serie S, genero G
                            WHERE		A.fk_exemplar_id = E.id AND
                                        (E.fk_edicao_numero, E.fk_edicao_data_lanc, E.fk_edicao_nome_intern, E.fk_edicao_ciclo_de_num) =
                                        (ED.numero, ED.data_lanc, ED.fk_serie_nome_intern, ED.fk_serie_ciclo_de_num) AND
                                        (ED.fk_serie_nome_intern, ED.fk_serie_ciclo_de_num) = (S.nome_intern, S.ciclo_de_num) AND
                                        (G.fk_serie_ciclo_de_num, G.fk_serie_nome_intern) = (S.ciclo_de_num, S.nome_intern) AND
                                        A.fk_colecao_nome_colecao like '{nome_col}' AND
                                        A.fk_colecao_email like '{_email}'
                            GROUP BY 	G.fk_serie_nome_intern, G.fk_serie_ciclo_de_num, G.genero)
                GROUP BY 	G.genero
                ORDER BY	top_3 DESC, G.genero
            
            '''
        )

        consulta4 = (
            f''' 
                
               SELECT	C.fk_contribuidor_nome, count(*) as contagem
                FROM	contribui C
                WHERE 	(C.fk_serie_nome_intern, C.fk_serie_ciclo_de_num, C.fk_contribuidor_nome) in
                        (SELECT		S.nome_intern, S.ciclo_de_num, C.fk_contribuidor_nome
                        FROM		agrega A, exemplar E, edicao ED, serie S, contribui C
                        WHERE		A.fk_exemplar_id = E.id AND
                                    (E.fk_edicao_numero, E.fk_edicao_data_lanc, E.fk_edicao_nome_intern, E.fk_edicao_ciclo_de_num) =
                                    (ED.numero, ED.data_lanc, ED.fk_serie_nome_intern, ED.fk_serie_ciclo_de_num) AND
                                    (ED.fk_serie_nome_intern, ED.fk_serie_ciclo_de_num) = (S.nome_intern, S.ciclo_de_num) AND
                                    (C.fk_serie_nome_intern, C.fk_serie_ciclo_de_num) = (S.nome_intern, S.ciclo_de_num) AND
                                    A.fk_colecao_nome_colecao like '{nome_col}' AND
                                    A.fk_colecao_email like '{_email}' AND
                                    C.funcao ilike 'Roteirista%'
                        GROUP BY	S.nome_intern, S.ciclo_de_num, C.fk_contribuidor_nome)
                GROUP BY C.fk_contribuidor_nome
                ORDER BY	contagem desc
            
            '''
        )
        consulta5 = (
            f''' 
                
                SELECT	C.fk_contribuidor_nome, count(*) as contagem
                FROM	contribui C
                WHERE 	(C.fk_serie_nome_intern, C.fk_serie_ciclo_de_num, C.fk_contribuidor_nome) in
                        (SELECT		S.nome_intern, S.ciclo_de_num, C.fk_contribuidor_nome
                        FROM		agrega A, exemplar E, edicao ED, serie S, contribui C
                        WHERE		A.fk_exemplar_id = E.id AND
                                    (E.fk_edicao_numero, E.fk_edicao_data_lanc, E.fk_edicao_nome_intern, E.fk_edicao_ciclo_de_num) =
                                    (ED.numero, ED.data_lanc, ED.fk_serie_nome_intern, ED.fk_serie_ciclo_de_num) AND
                                    (ED.fk_serie_nome_intern, ED.fk_serie_ciclo_de_num) = (S.nome_intern, S.ciclo_de_num) AND
                                    (C.fk_serie_nome_intern, C.fk_serie_ciclo_de_num) = (S.nome_intern, S.ciclo_de_num) AND
                                    A.fk_colecao_nome_colecao like '{nome_col}' AND
                                    A.fk_colecao_email like '{_email}' AND
                                    C.funcao ilike '%Desenhista'
                        GROUP BY	S.nome_intern, S.ciclo_de_num, C.fk_contribuidor_nome)
                GROUP BY C.fk_contribuidor_nome
                ORDER BY	contagem desc
            
            '''
        )
        consulta6 = (
            f''' 
                
                SELECT	C.fk_contribuidor_nome, count(*) as contagem
                FROM	contribui C
                WHERE 	(C.fk_serie_nome_intern, C.fk_serie_ciclo_de_num, C.fk_contribuidor_nome) in
                        (SELECT		S.nome_intern, S.ciclo_de_num, C.fk_contribuidor_nome
                        FROM		agrega A, exemplar E, edicao ED, serie S, contribui C
                        WHERE		A.fk_exemplar_id = E.id AND
                                    (E.fk_edicao_numero, E.fk_edicao_data_lanc, E.fk_edicao_nome_intern, E.fk_edicao_ciclo_de_num) =
                                    (ED.numero, ED.data_lanc, ED.fk_serie_nome_intern, ED.fk_serie_ciclo_de_num) AND
                                    (ED.fk_serie_nome_intern, ED.fk_serie_ciclo_de_num) = (S.nome_intern, S.ciclo_de_num) AND
                                    (C.fk_serie_nome_intern, C.fk_serie_ciclo_de_num) = (S.nome_intern, S.ciclo_de_num) AND
                                    A.fk_colecao_nome_colecao like '{nome_col}' AND
                                    A.fk_colecao_email like '{_email}' AND
                                    C.funcao ilike 'Mangaka'
                        GROUP BY	S.nome_intern, S.ciclo_de_num, C.fk_contribuidor_nome)
                GROUP BY C.fk_contribuidor_nome
                ORDER BY	contagem desc
            
            '''
        )
        consulta7 = (
            f''' 
                
                
                SELECT	M.demografia, count(*) as contagem
                FROM	manga M, serie S
                WHERE 	(S.nome_intern, M.demografia) in
                        (SELECT		S.nome_intern, M.demografia
                        FROM		agrega A, exemplar E, edicao ED, serie S, manga M
                        WHERE		A.fk_exemplar_id = E.id AND
                                    (E.fk_edicao_numero, E.fk_edicao_data_lanc, E.fk_edicao_nome_intern, E.fk_edicao_ciclo_de_num) =
                                    (ED.numero, ED.data_lanc, ED.fk_serie_nome_intern, ED.fk_serie_ciclo_de_num) AND
                                    (ED.fk_serie_nome_intern, ED.fk_serie_ciclo_de_num) = (S.nome_intern, S.ciclo_de_num) AND
                                    (M.fk_serie_nome_intern, M.fk_serie_ciclo_de_num) = (S.nome_intern, S.ciclo_de_num) AND
                                    A.fk_colecao_nome_colecao ilike '{nome_col}' AND
                                    A.fk_colecao_email like '{_email}'
                        GROUP BY	S.nome_intern, M.demografia)
                GROUP BY M.demografia
                ORDER BY	contagem desc, M.demografia
            
            '''
        )
        consulta8 = (
            f''' 
                
                SELECT	DATE_TRUNC('month',E.data_aquis) as meses, COUNT(*)
                FROM	agrega A, exemplar E
                WHERE	A.fk_exemplar_id = E.id AND
                        A.fk_colecao_nome_colecao like '{nome_col}' AND
                        A.fk_colecao_email like '{_email}'
                GROUP BY meses
                ORDER BY meses ASC
            
            '''
        )

        try:
            global r1
            r1 = selecao(connection,consulta1)
            global r2
            r2 = selecao(connection,consulta2)
            global r3
            r3 = selecao(connection,consulta3)
            global r4
            r4 = selecao(connection,consulta4)
            global r5
            r5 = selecao(connection,consulta5)
            global r6
            r6 = selecao(connection,consulta6)
            global r7
            r7 = selecao(connection,consulta7)
            global r8
            r8 = selecao(connection,consulta8)
            count = 0
            temp = []
            for linhas in r3:
                if count < 3:
                    temp.append(linhas)
                    count+=1
            r3 = temp

            count = 0
            count2 = 0
            eixo_meses = [] # Eixo X do gráfico
            total_exemplares_mes = [] # Eixo Y do gráfico
            somatorio = 0
            if len(r8)<6:
                for mes in r8:
                    somatorio+=mes[1]
                    total_exemplares_mes.append(somatorio)
                    temp_mes = mes[0].strftime("%b - %Y")
                    echo(f"Eixo meses: {temp_mes}")
                    eixo_meses.append(temp_mes)
                    count+=1
            else:
                for mes in r8:
                    somatorio+=mes[1]
                    if count >= len(r8)-5:
                        total_exemplares_mes.append(somatorio)
                        temp_mes = mes[0].strftime("%b - %Y")
                        echo(f"Eixo meses: {temp_mes}")
                        eixo_meses.append(temp_mes)
                        count2+=1
                    count+=1

            if os.path.exists("static/grafico.png"):
                os.remove("static/grafico.png")

            matplotlib.rc('axes',edgecolor='#c04f3b')
            matplotlib.rc('xtick',color='#c04f3b')
            matplotlib.rc('xtick',labelcolor='#c6dce4')
            matplotlib.rc('ytick',color='#c04f3b')
            matplotlib.rc('ytick',labelcolor='#c6dce4')
            matplotlib.rcParams["axes.linewidth"] = 2.50

            plt.yticks(np.arange(min(total_exemplares_mes), max(total_exemplares_mes)+1))
            plt.grid()
            plt.plot(eixo_meses, total_exemplares_mes, 'b-', color='#c6dce4')
            plt.plot(eixo_meses, total_exemplares_mes, 'o', color='#c04f3b')
            plt.savefig('static/grafico.png', transparent=True)
            plt.close()
            

        except OperationalError as e:
            echo(f"O erro {e} ocorreu. Tente novamente.")
        
    return user(r1, r2, r3, r4, r5, r6, r7, r8)


@app.route('/criar_colecao', methods=['POST'])
def criar_colecao():

    if request.method == 'POST':
        
        criar_col = request.form['nome_colecao_nova']

        consulta = (
            f''' 
            
            INSERT INTO Colecao (nome_colecao, fk_colecionador_email)
            VALUES 
            ('{criar_col}', '{_email}')

            '''
        )

        try:
            execute_query(connection, consulta)
        except OperationalError as e:
            echo(f"O erro {e} ocorreu. Tente novamente.")
    return redirect(url_for('adm_colecoes'))


@app.route('/editar_colecao', methods=['POST'])
def editar_colecao():

    if request.method == 'POST':
        
        novo_nome = request.form['editar_nome_colecao']
        nome_antigo = request.form['escolha']

        consulta = (
            f''' 
            
            UPDATE colecao set nome_colecao = '{novo_nome}' 
            WHERE fk_colecionador_email like '{_email}' and
            nome_colecao like '{nome_antigo}'
            '''
        )

        try:
            execute_query(connection, consulta)
        except OperationalError as e:
            echo(f"O erro {e} ocorreu. Tente novamente.")
    return redirect(url_for('adm_colecoes'))


@app.route('/deletar_colecao', methods=['POST'])
def deletar_colecao():

    if request.method == 'POST':
        
        nome_antigo = request.form['escolha']

        consulta = (
            f''' 
            
            DELETE FROM exemplar where id in (
									SELECT		A.fk_exemplar_id AS IDS
									FROM		agrega A JOIN exemplar E on (fk_exemplar_id = id)
									WHERE		A.fk_colecao_email like '{_email}'
												AND A.fk_colecao_nome_colecao like '{nome_antigo}'
									GROUP BY	ids);

            DELETE FROM colecao where fk_colecionador_email like '{_email}' and nome_colecao like '{nome_antigo}'

            '''
        )

        try:
            execute_query(connection, consulta)
        except OperationalError as e:
            echo(f"O erro {e} ocorreu. Tente novamente.")
    return redirect(url_for('adm_colecoes'))    

@app.route('/remover_exemplar/<nome_col>', methods=['POST'])
def remover_exemplar(nome_col):

    if request.method == 'POST':
        del_ex = request.form['del-exemplar']
        del_ex= str(del_ex)
        del_ex = del_ex.replace('+', ' ')
        del_ex = del_ex.split('_')
        
        consulta = (
            f'''
            DELETE FROM exemplar where id = {del_ex[3]}
            
            '''
        )

        try:
            execute_query(connection, consulta)
        except OperationalError as e:
            echo(f"O erro {e} ocorreu. Tente novamente.")

        return redirect(url_for('user_colecao', nome = nome_col))

@app.context_processor
def inject_email():
    return dict(email=_email)


@app.context_processor
def inject_username():
    return dict(username=_username)

@app.route('/voltar')
def voltar():
    return redirect(url_for('layouts'))


if __name__ == '__main__':
    app.run(debug=True)