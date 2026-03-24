// Aguarda o DOM carregar completamente
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎮 Jogo Rick and Morty carregado!');
    
    // Pegar dados do servidor
    const gameData = document.getElementById('game-data');
    const modoAtual = gameData ? gameData.dataset.modoAtual : 'normal';
    const tempoRestante = parseInt(gameData ? gameData.dataset.tempoRestante : 0);
    const mostrarJogo = gameData ? gameData.dataset.mostrarJogo === 'True' : false;
    const corretoId = parseInt(gameData ? gameData.dataset.corretoId : 0);
    
    // Configurar botões de opção
    const opcoesBtns = document.querySelectorAll('.opcao-btn');
    opcoesBtns.forEach(button => {
        button.addEventListener('click', function(e) {
            const palpite = this.dataset.palpite;
            const palpiteInput = document.getElementById('palpite');
            if (palpiteInput) {
                palpiteInput.value = palpite;
            }
            
            // Efeito visual
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 200);
        });
    });
    
    // Configurar botão de dica
    const btnDica = document.querySelector('.botao-dica');
    if (btnDica) {
        btnDica.addEventListener('click', function() {
            buscarDica(corretoId);
        });
    }
    
    // Iniciar timer se estiver no modo tempo
    if (modoAtual === 'tempo' && tempoRestante > 0 && mostrarJogo) {
        iniciarTimer(tempoRestante);
    }
});

// Função para buscar dica
function buscarDica(personagemId) {
    const btnDica = document.querySelector('.botao-dica');
    const dicaDiv = document.getElementById('dica-texto');
    
    if (!btnDica || !dicaDiv) {
        console.error('Elementos não encontrados');
        return;
    }
    
    btnDica.disabled = true;
    btnDica.textContent = '🔄 Carregando...';
    
    fetch('/dica/' + personagemId)
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro na requisição');
            }
            return response.json();
        })
        .then(data => {
            dicaDiv.textContent = data.dica;
            dicaDiv.style.display = 'block';
            
            // Esconder a dica após 5 segundos
            setTimeout(() => {
                dicaDiv.style.display = 'none';
            }, 5000);
        })
        .catch(error => {
            console.error('Erro ao buscar dica:', error);
            dicaDiv.textContent = '❌ Erro ao carregar dica. Tente novamente!';
            dicaDiv.style.display = 'block';
            
            setTimeout(() => {
                dicaDiv.style.display = 'none';
            }, 3000);
        })
        .finally(() => {
            btnDica.disabled = false;
            btnDica.textContent = '🔍 DICA';
        });
}

// Função para iniciar o timer
function iniciarTimer(tempoInicial) {
    let tempoRestante = tempoInicial;
    const timerInterval = setInterval(function() {
        if (tempoRestante <= 0) {
            clearInterval(timerInterval);
            alert('⏰ TEMPO ESGOTADO! O jogo será resetado.');
            window.location.reload();
        } else {
            tempoRestante--;
            
            const timerBar = document.querySelector('.timer-bar');
            const timerText = document.querySelector('.timer-text');
            
            if (timerBar && timerText) {
                const percent = (tempoRestante / 30) * 100;
                timerBar.style.width = percent + '%';
                timerText.textContent = '⏱️ Tempo: ' + tempoRestante + 's';
                
                if (tempoRestante <= 5) {
                    timerBar.style.backgroundColor = '#ff4444';
                }
            }
        }
    }, 1000);
}

// Adicionar animações CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .dica-texto {
        animation: fadeIn 0.5s ease-out;
        background: rgba(0, 0, 0, 0.9);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
        border-left: 4px solid #ff9800;
        display: none;
        color: white;
    }
    
    .opcao-btn {
        transition: transform 0.2s;
        cursor: pointer;
    }
    
    .opcao-btn:active {
        transform: scale(0.95);
    }
    
    .timer-bar {
        transition: width 0.3s linear, background-color 0.3s;
    }
    
    .botao-dica:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
`;

document.head.appendChild(style);