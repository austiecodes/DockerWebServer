import crypt


def test_passwd(user_name: str, passwd: str) -> bool:
    pass_file = open('/etc/shadow')
    for line in pass_file.readlines():
        if ":" in line:
            user = line.split(":")[0]
            if user != user_name:
                continue
            crypt_pass = line.split(":")[1].strip(' ')
            salt = crypt_pass[crypt_pass.find("$"):crypt_pass.rfind("$")]
            crypt_word = crypt.crypt(passwd, salt)
            return crypt_word == crypt_pass
    return False


# 判断容器是否属于某个用户
def test_container(container: str, user_name: str) -> bool:
    if '_' in container:
        container_user_name, id = container.split('_')
        return container_user_name == user_name and id in ['a', 'b', 'c']
    return False
