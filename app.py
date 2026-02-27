from flask import Flask, render_template, session, request, jsonify, redirect, url_for
import requests
import random
from functools import wraps

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

def traduzir_personagem(dados):
    dados_traduzidos = dados.copy()
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

@app.route('/', methods=['GET', 'POST'])
def home():
    # Inicializar sessão
    if 'pontuacao' not in session:
        session['pontuacao'] = 0
        session['tentativas'] = 0
        session['sequencia'] = 0
        session['total_jogos'] = 0
        session['historico'] = []
    
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
                personagem = traduzir_personagem(correto.copy())
                opcoes = [p['name'] for p in personagens]
                random.shuffle(opcoes)
                mostrar_jogo = True
                session['total_jogos'] = session.get('total_jogos', 0) + 1
                
        elif 'verificar' in request.form:
            palpite = request.form['palpite']
            correto = session.get('correto', '')
            
            session['tentativas'] = session.get('tentativas', 0) + 1
            
            if palpite == correto:
                session['pontuacao'] = session.get('pontuacao', 0) + 1
                session['sequencia'] = session.get('sequencia', 0) + 1
                resultado = "acertou"
                mensagem_resultado = random.choice(frases_acerto)
                
               
                if 'historico' in session:
                    session['historico'].append({
                        'personagem': correto,
                        'resultado': 'acertou',
                        'sequencia': session['sequencia']
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
            
            personagens = buscar_personagens(4)
            if personagens:
                novo_correto = random.choice(personagens)
                session['correto'] = novo_correto['name']
                session['correto_id'] = novo_correto['id']
                personagem = traduzir_personagem(novo_correto.copy())
                opcoes = [p['name'] for p in personagens]
                random.shuffle(opcoes)
                mostrar_jogo = True
    
    if session.get('correto') and not mostrar_jogo and request.method != 'POST':
        mostrar_jogo = True
        try:
            resposta = requests.get(f"{ENDPOINT_API}/{session.get('correto_id')}", timeout=5)
            if resposta.status_code == 200:
                personagem = traduzir_personagem(resposta.json())
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
                         historico=session.get('historico', []))

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
            dicas = [
                f"📍 Origem: {dados['origin']['name']}",
                f"📍 Localização: {dados['location']['name']}",
                f"🎬 Aparece em {len(dados['episode'])} episódios"
            ]
            return jsonify({'dica': random.choice(dicas)})
    except:
        pass
    return jsonify({'dica': 'Sem dicas disponíveis'})

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