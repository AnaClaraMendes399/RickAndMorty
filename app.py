from flask import Flask, render_template, session, request, jsonify, redirect, url_for
import requests
import random
import time
from functools import wraps
from datetime import datetime

ENDPOINT_API = "https://rickandmortyapi.com/api/character"

# dicionario p/ portugues
traducoes = {
    'status': {
        'Alive': ' Vivo',
        'Dead': ' Morto',
        'unknown': ' Desconhecido'
    },
    'species': {
        'Human': ' Humano',
        'Alien': ' Alienígena',
        'Humanoid': ' Humanoide',
        'Robot': ' Robô',
        'Animal': ' Animal',
        'Mythological Creature': ' Criatura Mitológica',
        'Disease': ' Doença',
        'Poopybutthole': ' Sr. Poopybutthole',
        'Cronenberg': ' Cronenberg',
        'unknown': ' Desconhecida'
    },
    'gender': {
        'Male': ' Masculino',
        'Female': ' Feminino',
        'Genderless': ' Sem gênero',
        'unknown': ' Desconhecido'
    }
}

frases_acerto = [
    "🎉 EXCELENTE! VOCÊ É UM VERDADERO FÃ! 🎉",
    "⚡ WUBBA LUBBA DUB DUB! ACERTOU! ⚡",
    "👽 PARABÉNS! MUITO BEM! 👽",
    "🛸 ACERTOU! VOCÊ CONHECE MESMO A SÉRIE! 🛸",
    "🌟 PERFEITO! CONTINUE ASSIM! 🌟"
]

frases_erro = [
    "😢 QUE PENA! TENTE NOVAMENTE! 😢",
    "🔬 ATÉ O RICK ERRARIA AS VEZES! TENTE DE NOVO! 🔬",
    "👾 NÃO FOI DESSA VEZ! O IMPORTANTE É TENTAR! 👾",
    "⚗️ ERROU! MAS A CIÊNCIA É TENTATIVA E ERRO! ⚗️"
]

app = Flask(__name__)
app.secret_key = 'chave-secreta-super-segura-rickandmorty'

# Ranking (armazenado em memória - em produção usaria banco de dados)
ranking = []

def traduzir_personagem(dados, modo_sem_resposta=False):
    dados_traduzidos = dados.copy()
    
    if modo_sem_resposta:
        # Modo sem resposta: oculta informações
        dados_traduzidos['status'] = '???'
        dados_traduzidos['species'] = '???'
        dados_traduzidos['gender'] = '???'
    else:
        if 'status' in dados_traduzidos and dados_traduzidos['status'] in traducoes['status']:
            dados_traduzidos['status'] = traducoes['status'][dados_traduzidos['status']]
        if 'species' in dados_traduzidos and dados_traduzidos['species'] in traducoes['species']:
            dados_traduzidos['species'] = traducoes['species'][dados_traduzidos['species']]
        if 'gender' in dados_traduzidos and dados_traduzidos['gender'] in traducoes['gender']:
            dados_traduzidos['gender'] = traducoes['gender'][dados_traduzidos['gender']]
    
    return dados_traduzidos

# busca personagens aleatorios da API
def buscar_personagens(qtd=4):
    personagens = []
    ids = random.sample(range(1, 827), qtd)
    
    for id_personagem in ids:
        try:
            resposta = requests.get(f"{ENDPOINT_API}/{id_personagem}", timeout=5)
            if resposta.status_code == 200:
                personagens.append(resposta.json())
        except:
            continue
    return personagens

def calcular_nivel(pontuacao):
    if pontuacao < 5:
        return "Iniciante", "🌱"
    elif pontuacao < 15:
        return "Explorador", "🔍"
    elif pontuacao < 30:
        return "Fã", "⭐"
    elif pontuacao < 50:
        return "Especialista", "🏆"
    else:
        return "Mestre das Dimensões", "👑"

def calcular_pontuacao_ofensiva(pontuacao_base, sequencia, dificuldade):
    """Calcula pontuação com bônus de ofensiva e dificuldade"""
    bonus_sequencia = sequencia * 10  # 10 pontos por acerto consecutivo
    multiplicador = 1
    
    if dificuldade == 'facil':
        multiplicador = 1
    elif dificuldade == 'medio':
        multiplicador = 1.5
    elif dificuldade == 'dificil':
        multiplicador = 2
    
    pontos = (pontuacao_base + bonus_sequencia) * multiplicador
    return int(pontos)

@app.route('/', methods=['GET', 'POST'])
def home():
    # Inicializar sessão
    if 'pontuacao' not in session:
        session['pontuacao'] = 0
        session['tentativas'] = 0
        session['sequencia'] = 0
        session['total_jogos'] = 0
        session['historico'] = []
        session['modo_jogo'] = 'normal'  # normal, tempo, sem_resposta
        session['dificuldade'] = 'facil'  # facil, medio, dificil
        session['tempo_restante'] = 30
        session['ultimo_tempo'] = time.time()
    
    # Verificar tempo no modo por tempo
    if session.get('modo_jogo') == 'tempo' and session.get('tempo_restante', 0) > 0:
        tempo_passado = time.time() - session.get('ultimo_tempo', time.time())
        session['tempo_restante'] = max(0, session.get('tempo_restante', 30) - tempo_passado)
        session['ultimo_tempo'] = time.time()
        
        if session['tempo_restante'] <= 0:
            # Tempo esgotado!
            session['modo_jogo'] = 'normal'
            return redirect(url_for('reset'))
    
    personagem = None
    opcoes = []
    mostrar_jogo = False
    resultado = None
    mensagem_resultado = ""
    personagem_correto = None
    
    nivel, emoji_nivel = calcular_nivel(session['pontuacao'])
    
    if request.method == 'POST':
        if 'iniciar_jogo' in request.form:
            personagens = buscar_personagens(4)
            if personagens:
                correto = random.choice(personagens)
                session['correto'] = correto['name']
                session['correto_id'] = correto['id']
                session['correto_info'] = correto.copy()
                
                modo_sem_resposta = (session.get('modo_jogo') == 'sem_resposta')
                personagem = traduzir_personagem(correto.copy(), modo_sem_resposta)
                opcoes = [p['name'] for p in personagens]
                random.shuffle(opcoes)
                mostrar_jogo = True
                session['total_jogos'] = session.get('total_jogos', 0) + 1
                
                # Resetar tempo no modo por tempo
                if session.get('modo_jogo') == 'tempo':
                    session['tempo_restante'] = 30
                    session['ultimo_tempo'] = time.time()
                
        elif 'verificar' in request.form:
            palpite = request.form['palpite']
            correto = session.get('correto', '')
            
            session['tentativas'] = session.get('tentativas', 0) + 1
            
            if palpite == correto:
                # Calcular pontuação com ofensiva
                pontos_ganhos = calcular_pontuacao_ofensiva(
                    10, 
                    session.get('sequencia', 0),
                    session.get('dificuldade', 'facil')
                )
                session['pontuacao'] = session.get('pontuacao', 0) + pontos_ganhos
                session['sequencia'] = session.get('sequencia', 0) + 1
                resultado = "acertou"
                mensagem_resultado = random.choice(frases_acerto)
                mensagem_resultado += f" +{pontos_ganhos} pts!"
                
                # Adicionar ao ranking (usando a variável global)
                if session.get('pontuacao') > 0:
                    ranking.append({
                        'nome': 'Jogador',
                        'pontuacao': session['pontuacao'],
                        'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                        'dificuldade': session.get('dificuldade', 'facil')
                    })
                    # Manter apenas top 10
                    ranking.sort(key=lambda x: x['pontuacao'], reverse=True)
                    # Limitar para 10 itens
                    while len(ranking) > 10:
                        ranking.pop()
                
                if 'historico' in session:
                    session['historico'].append({
                        'personagem': correto,
                        'resultado': 'acertou',
                        'sequencia': session['sequencia'],
                        'pontos': pontos_ganhos
                    })
            else:
                session['sequencia'] = 0
                resultado = "errou"
                personagem_correto = correto
                mensagem_resultado = random.choice(frases_erro)
                
                if 'historico' in session:
                    session['historico'].append({
                        'personagem': correto,
                        'resultado': 'errou',
                        'palpite': palpite
                    })
            
            if len(session.get('historico', [])) > 5:
                session['historico'] = session['historico'][-5:]
            
            # Carregar próximo personagem
            personagens = buscar_personagens(4)
            if personagens:
                novo_correto = random.choice(personagens)
                session['correto'] = novo_correto['name']
                session['correto_id'] = novo_correto['id']
                session['correto_info'] = novo_correto.copy()
                
                modo_sem_resposta = (session.get('modo_jogo') == 'sem_resposta')
                personagem = traduzir_personagem(novo_correto.copy(), modo_sem_resposta)
                opcoes = [p['name'] for p in personagens]
                random.shuffle(opcoes)
                mostrar_jogo = True
                
        elif 'mudar_modo' in request.form:
            novo_modo = request.form['modo_jogo']
            session['modo_jogo'] = novo_modo
            return redirect(url_for('home'))
            
        elif 'mudar_dificuldade' in request.form:
            nova_dificuldade = request.form['dificuldade']
            session['dificuldade'] = nova_dificuldade
            return redirect(url_for('home'))
    
    if session.get('correto') and not mostrar_jogo and request.method != 'POST':
        mostrar_jogo = True
        try:
            resposta = requests.get(f"{ENDPOINT_API}/{session.get('correto_id')}", timeout=5)
            if resposta.status_code == 200:
                modo_sem_resposta = (session.get('modo_jogo') == 'sem_resposta')
                personagem = traduzir_personagem(resposta.json(), modo_sem_resposta)
        except:
            pass
    
    return render_template('index.html',
                         pontuacao=session['pontuacao'],
                         tentativas=session['tentativas'],
                         sequencia=session['sequencia'],
                         total_jogos=session['total_jogos'],
                         personagem=personagem,
                         opcoes=opcoes,
                         mostrar_jogo=mostrar_jogo,
                         resultado=resultado,
                         mensagem_resultado=mensagem_resultado,
                         nivel=nivel,
                         emoji_nivel=emoji_nivel,
                         personagem_correto=personagem_correto,
                         historico=session.get('historico', []),
                         ranking=ranking[:10],
                         modo_atual=session.get('modo_jogo', 'normal'),
                         dificuldade_atual=session.get('dificuldade', 'facil'),
                         tempo_restante=int(session.get('tempo_restante', 30)))

@app.route('/reset', methods=['POST'])
def reset():
    session.clear()
    return redirect(url_for('home'))

@app.route('/dica/<int:personagem_id>', methods=['GET'])
def dica(personagem_id):
    try:
        resposta = requests.get(f"{ENDPOINT_API}/{personagem_id}", timeout=5)
        if resposta.status_code == 200:
            dados = resposta.json()
            
            # Dicas mais úteis
            dicas_pool = [
                f"📍 Origem: {dados['origin']['name']}",
                f"📍 Localização atual: {dados['location']['name']}",
                f"🎬 Aparece em {len(dados['episode'])} episódios",
                f"🆔 ID do personagem: {dados['id']}",
                f"📝 Primeira aparição: Episódio {dados['episode'][0].split('/')[-1] if dados['episode'] else '?'}"
            ]
            
            # Adicionar dica específica baseada no nome
            nome = dados['name'].lower()
            if 'rick' in nome:
                dicas_pool.append("🔬 Wubba Lubba Dub Dub! É um cientista!")
            elif 'morty' in nome:
                dicas_pool.append("😰 Oh geez! É um adolescente muito nervoso!")
            elif 'summer' in nome:
                dicas_pool.append("📱 É uma adolescente que adora celular!")
            
            return jsonify({'dica': random.choice(dicas_pool)})
    except:
        pass
    return jsonify({'dica': 'Sem dicas disponíveis. Tente novamente!'})

@app.route('/limpar_ranking', methods=['POST'])
def limpar_ranking():
    global ranking
    ranking = []
    return redirect(url_for('home'))

# ========== ERROS ==========
@app.errorhandler(404)
def pagina_nao_encontrada(error):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Erro 404</title>
        <style>
            body { 
                background: #0b1e2a;
                color: white;
                text-align: center;
                padding: 50px;
                font-family: Arial;
            }
            h1 { color: #b2d45c; font-size: 80px; margin: 0; }
            a { 
                background: #b2d45c;
                color: #0b1e2a;
                padding: 10px 30px;
                text-decoration: none;
                border-radius: 30px;
                display: inline-block;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <h1>404</h1>
        <h2>Página não encontrada!</h2>
        <p>Parece que você caiu em outra dimensão...</p>
        <a href="/">Voltar para o jogo</a>
    </body>
    </html>
    """, 404

@app.errorhandler(500)
def erro_servidor(error):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Erro 500</title>
        <style>
            body { 
                background: #0b1e2a;
                color: white;
                text-align: center;
                padding: 50px;
                font-family: Arial;
            }
            h1 { color: #ff6b6b; font-size: 80px; margin: 0; }
            a { 
                background: #ff6b6b;
                color: white;
                padding: 10px 30px;
                text-decoration: none;
                border-radius: 30px;
                display: inline-block;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <h1>500</h1>
        <h2>Erro no servidor!</h2>
        <p>O Rick já está consertando...</p>
        <a href="/">Tentar novamente</a>
    </body>
    </html>
    """, 500

if __name__ == '__main__':
    app.run(debug=True)