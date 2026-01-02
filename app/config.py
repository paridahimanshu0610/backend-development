from pydantic_settings import BaseSettings, SettingsConfigDict

# As per Pydantic version 1
# class Settings(BaseSettings):
#     database: str
#     database_hostname: str
#     database_port: str
#     database_password: str
#     database_name: str
#     database_username: str
#     secret_key: str
#     algorithm: str
#     access_token_expire_minutes: int

#     # In Pydantic (v1) and SQLModel, the nested Config class has a special meaning: 
#     # It is a declarative configuration pattern. Pydantic looks for a class literally named Config and uses its attributes to control behaviour.
#     class Config:
#         env_file = ".env"


# As per Pydantic version 2
class Settings(BaseSettings):
    database: str
    database_hostname: str
    database_port: int
    database_username: str
    database_password: str
    database_name: str

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

settings = Settings()
