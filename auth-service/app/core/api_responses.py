"""Exemplos de respostas de erro para o Swagger (OpenAPI).

FastAPI só documenta automaticamente o código de sucesso e o 422 de validação.
Os dicionários aqui cobrem os códigos de erro que as rotas realmente podem
devolver, com um payload de exemplo real (mesmo `detail` usado no código).
"""

UNAUTHORIZED = {
    401: {
        "description": "Não autenticado (token ausente, inválido ou expirado)",
        "content": {
            "application/json": {
                "examples": {
                    "sem_token": {"value": {"detail": "Não autenticado"}},
                    "token_invalido": {"value": {"detail": "Token inválido ou expirado"}},
                }
            }
        },
    }
}


def forbidden(permission: str) -> dict:
    return {
        403: {
            "description": "Autenticado, mas sem a permissão necessária",
            "content": {
                "application/json": {
                    "example": {"detail": f"Acesso negado: permissão '{permission}' necessária"}
                }
            },
        }
    }


NOT_FOUND_USER = {
    404: {
        "description": "Usuário não encontrado",
        "content": {"application/json": {"example": {"detail": "Usuário não encontrado"}}},
    }
}

EMAIL_JA_CADASTRADO = {
    400: {
        "description": "E-mail já cadastrado",
        "content": {"application/json": {"example": {"detail": "E-mail já cadastrado"}}},
    }
}

CADASTRO_ADMIN_PROIBIDO = {
    403: {
        "description": "Tentativa de se autocadastrar como admin",
        "content": {
            "application/json": {
                "example": {"detail": "O papel de administrador não pode ser escolhido no cadastro público"}
            }
        },
    }
}

CREDENCIAIS_INVALIDAS = {
    401: {
        "description": "E-mail ou senha incorretos",
        "content": {"application/json": {"example": {"detail": "E-mail ou senha incorretos"}}},
    }
}

RESET_TOKEN_INVALIDO = {
    400: {
        "description": "Token de redefinição inválido, expirado, já usado ou senha fraca",
        "content": {
            "application/json": {
                "examples": {
                    "inexistente": {"value": {"detail": "Token de recuperação inválido ou inexistente."}},
                    "expirado": {
                        "value": {
                            "detail": "O link de recuperação expirou (validade de 30 minutos). Solicite uma nova recuperação."
                        }
                    },
                    "ja_usado": {"value": {"detail": "Este link de recuperação já foi utilizado anteriormente."}},
                    "senha_curta": {"value": {"detail": "A nova senha deve ter no mínimo 6 caracteres."}},
                }
            }
        },
    }
}
