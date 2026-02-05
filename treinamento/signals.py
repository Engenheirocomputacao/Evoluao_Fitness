from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from .models import Individuo, Treinamento, RegistroTreinamento

@receiver(post_migrate)
def create_groups_and_permissions(sender, **kwargs):
    """
    Cria grupos e permissões personalizadas após as migrações
    """
    
    # Criar grupo de administradores do sistema
    admin_group, created = Group.objects.get_or_create(name='Administradores')
    if created:
        # Adicionar todas as permissões para administradores
        content_types = ContentType.objects.filter(app_label='treinamento')
        for content_type in content_types:
            permissions = Permission.objects.filter(content_type=content_type)
            admin_group.permissions.add(*permissions)
    
    # Criar grupo de usuários regulares
    user_group, created = Group.objects.get_or_create(name='Usuários')
    if created:
        # Permissões para usuários regulares
        models = [Individuo, RegistroTreinamento]
        for model in models:
            content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(
                content_type=content_type,
                codename__in=['add_' + model.__name__.lower(), 
                             'change_' + model.__name__.lower(), 
                             'view_' + model.__name__.lower()]
            )
            user_group.permissions.add(*permissions)
    
    # Criar grupo de instrutores/personal trainers
    trainer_group, created = Group.objects.get_or_create(name='Instrutores')
    if created:
        # Permissões para instrutores (podem ver todos os registros)
        content_type = ContentType.objects.get_for_model(RegistroTreinamento)
        permissions = Permission.objects.filter(
            content_type=content_type,
            codename__in=['view_registrotreinamento']
        )
        trainer_group.permissions.add(*permissions)
        
        # Também podem gerenciar treinamentos
        content_type = ContentType.objects.get_for_model(Treinamento)
        permissions = Permission.objects.filter(
            content_type=content_type,
            codename__in=['add_treinamento', 'change_treinamento', 'view_treinamento']
        )
        trainer_group.permissions.add(*permissions)