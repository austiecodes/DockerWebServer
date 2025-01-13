import crypt


def check_password(username: str, passwd: str) -> bool:
    passFile = open('/etc/shadow')
    for line in passFile.readlines():
        if ":" in line:
            user = line.split(":")[0]
            if user != username:
                continue
            cryptPass = line.split(":")[1].strip(' ')
            salt = cryptPass[cryptPass.find("$"):cryptPass.rfind("$")]
            cryptWord = crypt.crypt(passwd, salt)
            return cryptWord == cryptPass
    return False


# 判断容器是否属于某个用户
def check_container(container: str, username: str) -> bool:
    if '_' in container:
        uname, id = container.split('_')
        return uname == username and id in ['a', 'b', 'c']
    return False
