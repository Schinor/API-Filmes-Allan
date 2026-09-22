"""Exemplos de respostas de erro para o Swagger (OpenAPI).

FastAPI só documenta automaticamente o código de sucesso e o 422 de validação.
Os dicionários aqui cobrem os códigos de erro que as rotas realmente podem
devolver, com um payload de exemplo real (mesmo `detail` usado no código).
"""

UNAUTHORIZED = {
    401: {
        "description": "Não autenticado (token ausente ou inválido)",
        "content": {
            "application/json": {
                "examples": {
                    "sem_token": {"value": {"detail": "Token não enviado"}},
                    "token_invalido": {"value": {"detail": "Token inválido ou expirado"}},
                }
            }
        },
    }
}


def forbidden(permission: str) -> dict:
    return {
        403: {
            "description": "Autenticado, mas sem a permissão necessária (evento 'acesso_negado' é registrado na auditoria)",
            "content": {
                "application/json": {
                    "example": {"detail": f"Acesso negado: permissão '{permission}' necessária"}
                }
            },
        }
    }


AUTH_SERVICE_INDISPONIVEL = {
    503: {
        "description": "auth-service inacessível",
        "content": {
            "application/json": {
                "example": {"detail": "Serviço de autenticação inacessível: ..."}
            }
        },
    }
}

LOG_SERVICE_INDISPONIVEL = {
    503: {
        "description": "log-service inacessível",
        "content": {"application/json": {"example": {"detail": "Serviço de auditoria indisponível"}}},
    }
}

CREDENCIAIS_INVALIDAS = {
    401: {
        "description": "E-mail ou senha incorretos",
        "content": {"application/json": {"example": {"detail": "E-mail ou senha incorretos"}}},
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

NOT_FOUND_USER = {
    404: {
        "description": "Usuário não encontrado",
        "content": {"application/json": {"example": {"detail": "Usuário não encontrado"}}},
    }
}

RESET_TOKEN_INVALIDO = {
    400: {
        "description": "Token de redefinição inválido, expirado, já usado ou senha fraca",
        "content": {
            "application/json": {
                "examples": {
                    "inexistente": {"value": {"detail": "Token de recuperação inválido ou inexistente."}},
                    "senha_curta": {"value": {"detail": "A nova senha deve ter no mínimo 6 caracteres."}},
                }
            }
        },
    }
}

TMDB_INDISPONIVEL = {
    502: {
        "description": "Erro ao consultar a API do TMDB",
        "content": {
            "application/json": {"example": {"detail": "Erro ao consultar TMDB: <motivo>"}}
        },
    }
}

FAVORITO_DUPLICADO = {
    409: {
        "description": "Filme já está nos favoritos do usuário",
        "content": {"application/json": {"example": {"detail": "Filme já está nos favoritos"}}},
    }
}

FAVORITO_NAO_ENCONTRADO = {
    404: {
        "description": "Favorito não encontrado para este usuário",
        "content": {"application/json": {"example": {"detail": "Favorito não encontrado"}}},
    }
}

COMENTARIO_NAO_ENCONTRADO = {
    404: {
        "description": "Comentário não encontrado",
        "content": {"application/json": {"example": {"detail": "Comentário não encontrado"}}},
    }
}
