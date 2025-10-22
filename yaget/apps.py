from django.apps import AppConfig

class YagetConfig(AppConfig):
    name = 'yaget'
    qoo_conf_list = ''
    verbose_name = ''

    def ready(self):
        verbose_name = 'testtest.' # これはうまく保持できていない・・
        return