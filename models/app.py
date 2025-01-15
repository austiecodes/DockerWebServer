from pydantic import BaseModel


class HostConfig(BaseModel):
    Name: str
    Port: int
    Key: str


class TinyDBConfig(BaseModel):
    GpuRequestDatabaseSavePath: str
    DockerImagesDatabaseSavePath: str
    UserInfoDatabaseSavePath: str


class DBConfig(BaseModel):
    Path: str


class MailConfig(BaseModel):
    MailLoginUser: str
    MailPassword: str
    MailSender: str
    FromStr: str
    ServerHost: str
    ServerPort: int
    UseSSL: bool
    MaxResendTime: int


class AdminConfig(BaseModel):
    AdministratorPasswd: str


class AppConfig(BaseModel):
    Host: HostConfig
    TinyDB: TinyDBConfig
    DB: DBConfig
    Mail: MailConfig
    Admin: AdminConfig
