# unbite

[English](README.md) · **Português (Brasil)**

**Um vigia pequeno para a webcam que avisa, na sua língua, quando a sua mão vai até a boca.**

Roer unha é quase sempre automático: acontece enquanto você lê código, espera um build ou assiste a uma IA escrever a resposta. Quando você percebe, a unha já foi. O `unbite` percebe por você. Ele roda quieto em segundo plano e, no momento em que a ponta de um dedo chega à boca, toca um bipe e mostra uma faixa vermelha dizendo *"Mão longe da boca"*, na língua do seu computador.

- **Privado de verdade.** Tudo roda no seu computador, com modelos do [MediaPipe](https://ai.google.dev/edge/mediapipe). Nenhuma imagem é salva, enviada ou compartilhada.
- **Fala a sua língua.** Usa o idioma do sistema; os alertas vêm em 22 idiomas. Com `--voice`, ele também fala o alerta em voz alta, com as vozes que já vêm no Windows, no macOS ou no Linux.
- **Sabe a diferença entre celular e unha.** Celular no ouvido, copo, garfo ou escova de dentes na mão não disparam o alerta.
- **Leve.** Roda só no processador, a 15 a 25 quadros por segundo, com uma webcam comum de notebook.

## Como funciona

```
quadro da webcam ─► pontos do rosto (boca) ─┐
                 └► pontos da mão (pontas dos dedos) ─► distância em "larguras de boca" ─► ficou ≥ 0,6 s? ─► alerta
                                                              │
                              só quando está perto ─► detector de objetos: celular, copo, comida...? ─► ignora
```

A distância é medida em larguras de boca, então funciona igual se você senta perto da tela ou se afasta. O detector de objetos, o modelo mais lento, só roda quando um dedo já está perto da boca.

## Instalação

Precisa de Python 3.10 ou mais novo e de uma webcam.

```bash
pip install git+https://github.com/icarocarvalhomessias/unbite
```

Ou a partir de um clone:

```bash
git clone https://github.com/icarocarvalhomessias/unbite
cd unbite
pip install .
```

Os três modelos (cerca de 19 MB) são baixados na primeira vez, conferidos por SHA-256 e guardados na sua pasta de usuário.

## Uso

```bash
unbite --preview        # primeira vez: ver o que a câmera vê e calibrar
unbite                  # uso normal: sem janela, só os alertas
```

Para parar, aperte `q` na janela de preview ou `Ctrl+C` no terminal.

| Opção | O que faz |
|---|---|
| `--preview` | Mostra a câmera, a boca, o dedo mais próximo e a distância. |
| `--threshold 0.9` | Distância (em larguras de boca) que conta como "na boca". Menor é mais rigoroso. |
| `--hold 0.6` | Segundos com a mão na boca antes de alertar, para ignorar gestos rápidos. |
| `--cooldown 4` | Segundos mínimos entre dois alertas. |
| `--camera N` / `--list-cameras` | Escolhe a câmera. Padrão: a última encontrada, normalmente a externa. |
| `--lang pt` / `--list-languages` | Força um idioma no lugar do idioma do sistema. |
| `--voice` | Também fala o alerta em voz alta ("Mão na boca. Cuidado!"). Desligado por padrão. |
| `--no-sound`, `--no-banner` | Desliga o bipe ou a faixa. |
| `--no-objects` | Alerta mesmo com celular, copo ou comida na mão. |
| `--log alertas.csv` | Anota o horário de cada alerta num CSV, para ver seus padrões. Só horários. |

### Calibrando

Rode `unbite --preview` e leve os dedos à boca. A linha entre a boca e o dedo mais próximo fica vermelha abaixo do limite. Se apoiar o queixo na mão dispara o alerta, diminua o `--threshold` (tente `0.7`). Se ele deixa passar quando você rói de verdade, aumente.

## Idiomas

Alemão, árabe, chinês (simplificado e tradicional), coreano, espanhol, francês, hebraico, hindi, holandês, indonésio, inglês, italiano, japonês, polonês, português, russo, sueco, tailandês, turco, ucraniano e vietnamita.

O alerta falado (`--voice`, opcional) usa as vozes do sistema: SAPI no Windows, `say` no macOS e `spd-say` ou `espeak-ng` no Linux. Se não houver voz instalada para o seu idioma, usa a voz padrão. Dá para instalar outras nas configurações de fala do sistema.

Cada idioma é um arquivo pequeno em [`src/unbite/locales/`](src/unbite/locales). Correções de quem fala a língua e idiomas novos são muito bem-vindos: copie o `en.json`, traduza as duas frases e abra um pull request.

## Limitações

- A distância é medida em 2D, então a mão na frente do rosto (mas não na boca) pode disparar. Ajuste o `--threshold`.
- Ele só vê você enquanto você está na frente da câmera.
- Texto da direita para a esquerda (árabe, hebraico) na faixa depende da versão do Tk; o alerta falado não é afetado.
- É um empurrãozinho, não um tratamento. Se roer unha machuca você, um médico ou um terapeuta de reversão de hábitos pode ajudar.

## Desenvolvimento

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"     # Windows: .venv\Scripts\pip
pytest
ruff check . && ruff format --check .
```

O código é dividido para que a lógica possa ser testada sem câmera:

| Módulo | Papel |
|---|---|
| `geometry.py` | Centro da boca, distância do dedo, caixas. Funções puras. |
| `tracker.py` | Quando alertar: tempo na boca, intervalo, tolerância de objeto na mão. |
| `detection.py` | Modelos de rosto, mão e objetos do MediaPipe. |
| `models.py` | Download dos modelos em versão fixa, com conferência de hash. |
| `i18n.py`, `locales/` | Detecção do idioma do sistema e textos dos alertas. |
| `speech.py`, `banner.py` | Alerta falado e faixa na tela. |
| `app.py`, `cli.py` | Laço principal e linha de comando. |

## Licença

[MIT](LICENSE). Os modelos do MediaPipe são do Google, sob a Apache License 2.0.
