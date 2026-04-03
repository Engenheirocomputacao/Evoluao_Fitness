from django import forms
from django.core.exceptions import ValidationError
from .models import Individuo, Treinamento, RegistroTreinamento, LetterCaptcha
from .iot_models import DispositivoIoT, ConfiguracaoDispositivo
from datetime import date

class IndividuoForm(forms.ModelForm):
    class Meta:
        model = Individuo
        fields = ['nome_completo', 'data_nascimento', 'peso', 'sexo', 'observacoes', 'avatar']
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'peso': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': 'Ex: 70.5'}),
            'sexo': forms.Select(choices=Individuo.SEXO_CHOICES),
            'observacoes': forms.Textarea(attrs={'rows': 2, 'maxlength': 500, 'placeholder': 'Ex: restrições alimentares, lesões, etc.'}),
        }
    
    def clean_nome_completo(self):
        nome = self.cleaned_data['nome_completo']
        # Remover espaços extras
        nome = ' '.join(nome.split())
        
        # Verificar se tem pelo menos duas palavras
        if len(nome.split()) < 2:
            raise ValidationError('Por favor, informe nome e sobrenome.')
        
        return nome
    
    def clean_data_nascimento(self):
        data_nasc = self.cleaned_data['data_nascimento']
        if data_nasc and data_nasc > date.today():
            raise ValidationError('A data de nascimento não pode ser futura.')
        if data_nasc and data_nasc < date(1900, 1, 1):
            raise ValidationError('Por favor, informe uma data de nascimento válida.')
        return data_nasc

class TreinamentoForm(forms.ModelForm):
    class Meta:
        model = Treinamento
        fields = ['nome', 'unidade_medida', 'descricao']
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean_nome(self):
        nome = self.cleaned_data['nome']
        # Verificar unicidade (case insensitive)
        if Treinamento.objects.filter(nome__iexact=nome).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Já existe um treinamento com este nome.')
        return nome

class RegistroTreinamentoForm(forms.ModelForm):
    class Meta:
        model = RegistroTreinamento
        fields = ['treinamento', 'data', 'valor_alcançado', 'duracao', 'esforco_percebido', 'observacoes']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'duracao': forms.TimeInput(attrs={'type': 'time', 'placeholder': 'HH:MM'}),
            'esforco_percebido': forms.NumberInput(attrs={'min': '1', 'max': '10', 'step': '1', 'placeholder': '1-10'}),
            'observacoes': forms.Textarea(attrs={'rows': 2, 'maxlength': 500}),
        }
    
    def __init__(self, *args, **kwargs):
        self.individuo = kwargs.pop('individuo', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar treinamentos ativos
        self.fields['treinamento'].queryset = Treinamento.objects.all()
    
    def clean_data(self):
        data = self.cleaned_data.get('data')
        
        # Se data for uma string (formato DD/MM/AAAA), converter para datetime
        if isinstance(data, str):
            from datetime import datetime
            try:
                # Tenta converter do formato DD/MM/AAAA para datetime
                data_obj = datetime.strptime(data, '%d/%m/%Y').date()
                
                # Verifica se a data é futura (permite até 30 dias no futuro para agendamentos)
                from datetime import timedelta
                max_data_futura = date.today() + timedelta(days=30)
                if data_obj > max_data_futura:
                    raise ValidationError('A data do registro não pode ser mais de 30 dias no futuro.')
                
                return data_obj
            except ValueError:
                # Se não for possível converter, tenta o formato padrão
                pass
        
        # Se não for string ou conversão falhar, aplica validação normal
        from datetime import timedelta
        max_data_futura = date.today() + timedelta(days=30)
        if data and isinstance(data, date) and data > max_data_futura:
            raise ValidationError('A data do registro não pode ser mais de 30 dias no futuro.')
        
        return data
    
    def clean_duracao(self):
        duracao = self.cleaned_data.get('duracao')
        
        # Se duracao for uma string (formato HH:MM), converter para timedelta
        if isinstance(duracao, str):
            from datetime import datetime, time
            import re
            try:
                # Verifica se está no formato HH:MM
                if re.match(r'^\d{1,2}:\d{2}$', duracao):
                    partes = duracao.split(':')
                    horas = int(partes[0])
                    minutos = int(partes[1])
                    
                    if 0 <= horas <= 23 and 0 <= minutos <= 59:
                        # Converte para formato time
                        return time(hour=horas, minute=minutos)
                    else:
                        raise ValidationError('Duração inválida. Horas devem ser 0-23 e minutos 0-59.')
                else:
                    raise ValidationError('Formato de duração inválido. Use HH:MM (ex: 01:30).')
            except ValueError:
                pass
        
        return duracao
    
    def clean_valor_alcançado(self):
        valor = self.cleaned_data['valor_alcançado']
        treinamento = self.cleaned_data.get('treinamento')
        
        if valor and treinamento:
            # Validações específicas por tipo de treinamento
            if treinamento.unidade_medida == 'min' and valor > 1440:  # 24 horas
                raise ValidationError('Valor inválido para minutos (máximo 1440 minutos/24 horas).')
            elif treinamento.unidade_medida == 'km' and valor > 1000:  # 1000 km
                raise ValidationError('Valor inválido para quilômetros (máximo 1000 km).')
            elif treinamento.unidade_medida == 'kg' and valor > 1000:  # 1000 kg
                raise ValidationError('Valor inválido para quilogramas (máximo 1000 kg).')
            elif treinamento.unidade_medida == 'rep' and valor > 10000:  # 10000 repetições
                raise ValidationError('Valor inválido para repetições (máximo 10000).')
        
        return valor
    
    def clean(self):
        cleaned_data = super().clean()
        # Removida a restrição de um registro por dia para permitir múltiplas atividades no mesmo dia
        return cleaned_data

class LetterCaptchaForm(forms.Form):
    """Formulário para validação do captcha de letras"""
    captcha_solution = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        """Compatível com LoginView, que passa request em get_form_kwargs."""
        # Remove parâmetros extras que o LoginView envia
        self.request = kwargs.pop('request', None)
        self.session_key = kwargs.pop('session_key', None)

        # Se não veio session_key explícita, usa a sessão atual
        if self.session_key is None and self.request is not None:
            if not self.request.session.session_key:
                self.request.session.create()
            self.session_key = self.request.session.session_key

        super().__init__(*args, **kwargs)
    
    def clean_captcha_solution(self):
        solution = self.cleaned_data.get('captcha_solution')
        if not solution:
            raise ValidationError('Por favor, digite as letras do captcha.')
        
        # Busca o captcha para esta sessão
        try:
            captcha = LetterCaptcha.objects.get(
                session_key=self.session_key,
                is_solved=False
            )
        except LetterCaptcha.DoesNotExist:
            raise ValidationError('Sessão de captcha inválida ou expirada.')
        
        # Verifica se a solução está correta
        if not captcha.verify_solution(solution):
            raise ValidationError('Captcha incorreto.')
        
        # Marca como resolvido
        captcha.is_solved = True
        captcha.save()
        
        return solution

class SimpleCaptchaForm(forms.Form):
    """Formulário simples com checkbox de captcha"""
    captcha_verified = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'captcha-checkbox'})
    )
    
    def clean_captcha_verified(self):
        verified = self.cleaned_data.get('captcha_verified')
        if not verified:
            raise ValidationError('Por favor, confirme que você não é um robô.')
        return verified


class DispositivoIoTForm(forms.ModelForm):
    class Meta:
        model = DispositivoIoT
        fields = ['device_id', 'nome', 'tipo', 'status', 'fabricante', 'modelo', 'firmware_version', 'mac_address', 'ip_address']
        widgets = {
            'device_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: ESP32_001'}),
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome amigável do dispositivo'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'fabricante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Espressif'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: ESP32-WROOM-32'}),
            'firmware_version': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1.0.0'}),
            'mac_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 00:1B:44:11:3A:B7'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 192.168.1.100'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.individuo = kwargs.pop('individuo', None)
        super().__init__(*args, **kwargs)
        
        # Define o proprietário como o indivíduo logado
        if self.individuo:
            self.instance.proprietario = self.individuo
    
    def clean_device_id(self):
        device_id = self.cleaned_data['device_id']
        # Verificar unicidade (case insensitive)
        if DispositivoIoT.objects.filter(device_id__iexact=device_id).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Já existe um dispositivo com este ID.')
        return device_id
    
    def clean_mac_address(self):
        mac = self.cleaned_data.get('mac_address')
        if mac:
            # Valida formato MAC address
            import re
            mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
            if not re.match(mac_pattern, mac):
                raise ValidationError('Formato de endereço MAC inválido. Use: XX:XX:XX:XX:XX:XX')
        return mac
    
    def clean_ip_address(self):
        ip = self.cleaned_data.get('ip_address')
        if ip:
            # Valida formato IP
            import re
            ip_pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
            if not re.match(ip_pattern, ip):
                raise ValidationError('Formato de endereço IP inválido.')
        return ip

class ConfiguracaoDispositivoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoDispositivo
        fields = ['intervalo_leitura', 'valor_minimo_alerta', 'valor_maximo_alerta', 
                 'criar_registro_automatico', 'treinamento_padrao', 'fator_calibracao', 'offset_calibracao']
        widgets = {
            'intervalo_leitura': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '3600', 'placeholder': 'Segundos'}),
            'valor_minimo_alerta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Valor mínimo para alerta'}),
            'valor_maximo_alerta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Valor máximo para alerta'}),
            'criar_registro_automatico': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'treinamento_padrao': forms.Select(attrs={'class': 'form-control'}),
            'fator_calibracao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': '1.000'}),
            'offset_calibracao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas treinamentos ativos
        self.fields['treinamento_padrao'].queryset = Treinamento.objects.all()

class SimpleCaptchaLoginForm(forms.Form):
    """Formulário de login com CAPTCHA simples"""
    username = forms.CharField(
        label='Usuário',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    captcha_verified = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'captcha-checkbox'})
    )
    
    def __init__(self, *args, **kwargs):
        """Compatível com LoginView, que passa request em get_form_kwargs."""
        # Remove parâmetros extras que o LoginView envia
        self.request = kwargs.pop('request', None)
        self.user_cache = None
        super().__init__(*args, **kwargs)
    
    def clean_captcha_verified(self):
        verified = self.cleaned_data.get('captcha_verified')
        if not verified:
            raise ValidationError('Por favor, confirme que você não é um robô.')
        return verified
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            from django.contrib.auth import authenticate
            self.user_cache = authenticate(username=username, password=password)
            if self.user_cache is None:
                raise ValidationError('Usuário ou senha incorretos.')
        
        return cleaned_data
    
    def get_user(self):
        return self.user_cache


class CaptchaLoginForm(forms.Form):
    """Formulário de login com captcha integrado"""
    username = forms.CharField(
        label='Usuário',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    captcha_text = forms.CharField(
        label='Digite as letras',
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Letras do captcha',
            'autocomplete': 'off'
        })
    )
    captcha_solution = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        """Compatível com LoginView, que passa request em get_form_kwargs."""
        # Remove parâmetros extras que o LoginView envia
        self.request = kwargs.pop('request', None)
        self.session_key = kwargs.pop('session_key', None)
        self.user_cache = None

        # Se não veio session_key explícita, usa a sessão atual (se houver request)
        if self.session_key is None and self.request is not None:
            if not self.request.session.session_key:
                self.request.session.create()
            self.session_key = self.request.session.session_key

        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            from django.contrib.auth import authenticate
            self.user_cache = authenticate(username=username, password=password)
            if self.user_cache is None:
                raise ValidationError('Usuário ou senha incorretos.')
        
        return cleaned_data
    
    def get_user(self):
        return self.user_cache
    
    def clean_captcha_text(self):
        user_input = self.cleaned_data.get('captcha_text')
        if not user_input:
            raise ValidationError('Por favor, digite as letras do captcha.')
        
        # Busca o captcha para esta sessão
        try:
            captcha = LetterCaptcha.objects.get(
                session_key=self.session_key,
                is_solved=False
            )
        except LetterCaptcha.DoesNotExist:
            raise ValidationError('Sessão de captcha inválida ou expirada.')
        
        # Verifica se a solução está correta
        if not captcha.verify_solution(user_input):
            raise ValidationError('Captcha incorreto.')
        
        # Marca como resolvido
        captcha.is_solved = True
        captcha.save()
        
        return user_input
