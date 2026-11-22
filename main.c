#include "raylib.h"
#include <stdbool.h>

#define MAX_PERSONAGENS 4

typedef struct {
    Rectangle bounds;      // Posição (x, y) e tamanho (largura, altura)
    Color cor;             // Cor temporária (substituível por Textura/Sprite)
    const char *nome;      // Identificação do personagem
    bool arrastando;       // Estado de interação com o toque/mouse
    Vector2 offsetToque;   // Evita que o boneco "pule" para o centro do dedo
} Personagem;

int main(void) {
    // 1. Configuração da Janela e Enquadramento Responsivo
    const int larguraVirtual = 1280;
    const int alturaVirtual = 720;

    SetConfigFlags(FLAG_WINDOW_RESIZABLE | FLAG_VSYNC_HINT);
    InitWindow(larguraVirtual, alturaVirtual, "Portal dos Mundos - Escola");
    SetTargetFPS(60);

    // Câmera 2D para garantir que o jogo nunca fique cortado em telas diferentes
    Camera2D camera = { 0 };
    camera.target = (Vector2){ 0.0f, 0.0f };
    camera.offset = (Vector2){ 0.0f, 0.0f };
    camera.rotation = 0.0f;
    camera.zoom = 1.0f;

    // 2. Inicialização dos Personagens na Escola
    Personagem personagens[MAX_PERSONAGENS] = {
        { { 220, 460, 75, 130 }, SKYBLUE, "Aluno 1", false, {0, 0} },
        { { 420, 460, 75, 130 }, PINK,    "Aluna 2", false, {0, 0} },
        { { 620, 460, 75, 130 }, ORANGE,  "Aluno 3", false, {0, 0} },
        { { 950, 430, 85, 150 }, PURPLE,  "Prof.",   false, {0, 0} }
    };

    int personagemSelecionado = -1;

    // 3. Loop Principal do Jogo
    while (!WindowShouldClose()) {
        // Ajusta o zoom automaticamente se a tela mudar de tamanho (PC ou Celular)
        float escalaX = (float)GetScreenWidth() / larguraVirtual;
        float escalaY = (float)GetScreenHeight() / alturaVirtual;
        camera.zoom = (escalaX < escalaY) ? escalaX : escalaY;

        // Converte o toque/clique da tela real para a coordenada interna do jogo
        Vector2 posicaoToque = GetScreenToWorld2D(GetMousePosition(), camera);

        // Detectar início do toque / clique para arrastar
        if (IsMouseButtonPressed(MOUSE_LEFT_BUTTON)) {
            // Verifica de trás para frente para pegar o personagem que está por cima
            for (int i = MAX_PERSONAGENS - 1; i >= 0; i--) {
                if (CheckCollisionPointRec(posicaoToque, personagens[i].bounds)) {
                    personagemSelecionado = i;
                    personagens[i].arrastando = true;
                    personagens[i].offsetToque.x = posicaoToque.x - personagens[i].bounds.x;
                    personagens[i].offsetToque.y = posicaoToque.y - personagens[i].bounds.y;
                    break;
                }
            }
        }

        // Atualizar posição enquanto mantém pressionado
        if (IsMouseButtonDown(MOUSE_LEFT_BUTTON) && personagemSelecionado != -1) {
            personagens[personagemSelecionado].bounds.x = posicaoToque.x - personagens[personagemSelecionado].offsetToque.x;
            personagens[personagemSelecionado].bounds.y = posicaoToque.y - personagens[personagemSelecionado].offsetToque.y;
        }

        // Soltar personagem
        if (IsMouseButtonReleased(MOUSE_LEFT_BUTTON) && personagemSelecionado != -1) {
            personagens[personagemSelecionado].arrastando = false;
            personagemSelecionado = -1;
        }

        // 4. Desenho e Imersão Visual (Renderização)
        BeginDrawing();
            ClearBackground((Color){ 25, 25, 30, 255 }); // Bordas laterais escuras se a proporção mudar

            BeginMode2D(camera);
                // Parede e Chão da Sala de Aula
                DrawRectangle(0, 0, larguraVirtual, 520, (Color){ 242, 232, 207, 255 });
                DrawRectangle(0, 520, larguraVirtual, 200, (Color){ 164, 116, 73, 255 });

                // Lousa Verde com Moldura de Madeira
                DrawRectangle(340, 80, 600, 280, (Color){ 110, 65, 35, 255 });
                DrawRectangle(355, 95, 570, 250, (Color){ 34, 87, 58, 255 });
                DrawText("PORTAL DOS MUNDOS - SALA 01", 435, 130, 24, WHITE);

                // Carteiras Escolares
                for (int c = 0; c < 3; c++) {
                    int posX = 180 + (c * 240);
                    DrawRectangle(posX, 550, 140, 20, BROWN);
                    DrawRectangle(posX + 15, 570, 15, 70, DARKGRAY);
                    DrawRectangle(posX + 110, 570, 15, 70, DARKGRAY);
                }

                // Desenhar Personagens
                for (int i = 0; i < MAX_PERSONAGENS; i++) {
                    // Sombra no chão para dar profundidade/imersão
                    DrawEllipse(
                        personagens[i].bounds.x + personagens[i].bounds.width / 2,
                        personagens[i].bounds.y + personagens[i].bounds.height,
                        35, 10, Fade(BLACK, 0.3f)
                    );

                    // Corpo do personagem (pode ser substituído por DrawTexture)
                    DrawRectangleRounded(personagens[i].bounds, 0.3f, 8, personagens[i].cor);

                    // Destaque visual quando estiver sendo arrastado
                    if (personagens[i].arrastando) {
                        DrawRectangleRoundedLines(personagens[i].bounds, 0.3f, 8, 4.0f, YELLOW);
                    }

                    DrawText(
                        personagens[i].nome,
                        personagens[i].bounds.x + 8,
                        personagens[i].bounds.y - 25,
                        18, DARKGRAY
                    );
                }
            EndMode2D();

            DrawText("Toque e arraste os personagens pela sala", 20, 20, 20, DARKGRAY);
        EndDrawing();
    }

    CloseWindow();
    return 0;
}
