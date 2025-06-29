
# 🧼💡 Lavadora Electrolux LWI13 no Home Assistant

Central de automações, scripts, cards, dicas e um patchzinho maroto pra integração custom.  
Testado com a **Electrolux LWI13**!

## 🧩 Integrações HACS

> **Pré-requisito:** Instale o [**HACS**](https://hacs.xyz/)  
> Se ainda não tem, não tem nem graça mexer com HA.

- [Electrolux Status](https://github.com/albaintor/homeassistant_electrolux_status)
- [Mushroom](https://github.com/piitaya/lovelace-mushroom)
- [Bubble Card](https://github.com/Clooos/Bubble-Card)
- [Card-mod](https://github.com/thomasloven/lovelace-card-mod)

## 🃏 Cards – Painel Visual

### Card Principal – Mushroom

Mostra status, tempo restante e programa ativo, já trocando cor/ícone conforme o estado!  
*Toque simples* navega, *segurar* executa ação inteligente.

```yaml
# Card principal usando mushroom-template-card (custom:mushroom-template-card)
type: custom:mushroom-template-card
primary: |-
  {% set state = states('sensor.electrolux_lavadora_appliancestate') %}
  {% if state == 'Running' or state == 'Paused' %}
    {% set status_text = 'Lavando' if state == 'Running' else 'Pausada' %}
    {% set total_minutes = states('sensor.electrolux_lavadora_timetoend') | int(0) %}
    {% set hours = total_minutes // 60 %}
    {% set minutes = total_minutes % 60 %}
    {% if hours > 0 %}
      {{ status_text }}: {{ hours }}h {{ minutes }}m restantes
    {% else %}
      {{ status_text }}: {{ minutes }}m restantes
    {% endif %}
  {% elif state == 'End of Cycle' %}
    Finalizado
  {% else %}
    Lavadora
  {% endif %}
secondary: >-
  {% set state = states('sensor.electrolux_lavadora_appliancestate') %} {% if
  state == 'Idle' or state == 'OFF' %}
    Desligada
  {% else %}
    {% set program_id = states('number.electrolux_lavadora_latamuserselections_programid') %}
    {% set PGM_MAP = {
      '10': 'Normal',
      '1': 'Pesado/Jeans',
      '2': 'Tira manchas',
      '5': 'Limpeza',
      '6': 'Roupa escura',
      '7': 'Colorida',
      '8': 'Brancas',
      '9': 'Delicado/Esporte',
      '11': 'Rápido'
    } %}
    {% set nome_programa = PGM_MAP[program_id] | default('N/D') %}
    {% set nivel_id = states('number.electrolux_lavadora_latamuserselections_washlevel') | string %}
    {% set NIVEL_MAP = {
      '1': 'Extra baixo',
      '2': 'Extra baixo / baixo',
      '3': 'Baixo',
      '4': 'Baixo / médio',
      '5': 'Médio',
      '6': 'Médio / alto',
      '7': 'Alto',
      '8': 'Alto / Edredom', 
      '9': 'Edredom'
    } %}
    {% set nome_nivel = NIVEL_MAP[nivel_id] | default('N/D') %}
    {{ nome_programa }} | {{ nome_nivel }}
  {% endif %}
icon: |-
  {% set state = states('sensor.electrolux_lavadora_appliancestate') %}
  {% if state == 'Running' %}
    hue:room-laundry
  {% elif state == 'Idle' or state == 'OFF' %}
    hue:room-laundry-off
  {% else %}
    hue:room-laundry
  {% endif %}
icon_color: |-
  {% set state = states('sensor.electrolux_lavadora_appliancestate') %}
  {% if state == 'Running' %}
    blue
  {% elif state == 'Paused' %}
    orange
  {% elif state == 'End of Cycle' %}
    green
  {% else %}
    disabled
  {% endif %}
badge_icon: |-
  {% if is_state('sensor.electrolux_lavadora_connectivitystate', 'Connected') %}
    mdi:wifi
  {% else %}
    mdi:wifi-off
  {% endif %}
badge_color: |-
  {% if is_state('sensor.electrolux_lavadora_connectivitystate', 'Connected') %}
    green
  {% else %}
    red
  {% endif %}
fill_container: true
layout: vertical
multiline_secondary: false
tap_action:
  action: navigate
  navigation_path: "#lavadora"
hold_action:
  action: perform-action
  perform_action: script.lavadora_acao_inteligente
  target: {}
double_tap_action:
  action: none
card_mod:
  style:
    .: |-
      ha-card {
        --icon-size: 60px;
        {% if is_state('sensor.electrolux_lavadora_appliancestate', 'Running') %}
          --spin-animation: spin 2s linear infinite;
        {% else %}
          --spin-animation: none;
        {% endif %}
      }
      mushroom-shape-icon {
        animation: var(--spin-animation);
      }
      @keyframes spin {
        from {
          transform: rotate(0deg);
        }
        to {
          transform: rotate(360deg);
        }
      }
```

> 🎨 Dá pra personalizar cor, animação, badge, texto… solta a criatividade!

### 💦 Bubble Card – Opções & Comandos

Tudo fácil de clicar, alternar, ligar, pausar, avançar etapa.  
Botões extras pra Enxágue, Turbo, e outros 💪.

```yaml
type: vertical-stack
cards:
  - type: custom:bubble-card
    card_type: pop-up
    hash: "#lavadora"
    name: ""
    icon: ""
    show_header: false
    show_state: false
    show_name: false
    show_icon: false
    scrolling_effect: false
    tap_action:
      action: none
    double_tap_action:
      action: none
    hold_action:
      action: none
    card_layout: normal
    slide_to_close_distance: "200"
    margin: 8px
    bg_opacity: "75"
    shadow_opacity: "25"
  - type: custom:mushroom-template-card
    primary: |-
      {% set state = states('sensor.electrolux_lavadora_appliancestate') %}
      {% if state == 'Running' or state == 'Paused' %}
        {% set status_text = 'Lavando' if state == 'Running' else 'Pausada' %}
        {% set total_minutes = states('sensor.electrolux_lavadora_timetoend') | int(0) %}
        {% set hours = total_minutes // 60 %}
        {% set minutes = total_minutes % 60 %}
        {% if hours > 0 %}
          {{ status_text }}: {{ hours }}h {{ minutes }}m restantes
        {% else %}
          {{ status_text }}: {{ minutes }}m restantes
        {% endif %}
      {% elif state == 'End of Cycle' %}
        Finalizado
      {% else %}
        Lavadora
      {% endif %}
    secondary: >-
      {% set state = states('sensor.electrolux_lavadora_appliancestate') %} {%
      if state == 'Idle' or state == 'OFF' %}
        {% set program_id = states('number.electrolux_lavadora_latamuserselections_programid') %}
        {% set PGM_MAP = {
          '10': 'Normal',
          '1': 'Pesado/Jeans',
          '2': 'Tira manchas',
          '5': 'Limpeza',
          '6': 'Roupa escura',
          '7': 'Colorida',
          '8': 'Brancas',
          '9': 'Delicado/Esporte',
          '11': 'Rápido'
        } %}
        {% set nome_programa = PGM_MAP[program_id] | default('N/D') %}
        {% set nivel_id = states('number.electrolux_lavadora_latamuserselections_washlevel') | string %}
        {% set NIVEL_MAP = {
          '1': 'Extra baixo',
          '2': 'Extra baixo / baixo',
          '3': 'Baixo',
          '4': 'Baixo / médio',
          '5': 'Médio',
          '6': 'Médio / alto',
          '7': 'Alto',
          '8': 'Alto / Edredom', 
          '9': 'Edredom'
        } %}
        {% set nome_nivel = NIVEL_MAP[nivel_id] | default('N/D') %}
        {{ nome_programa }} | {{ nome_nivel }}
      {% endif %}
    icon: hue:room-laundry
    icon_color: |-
      {% set state = states('sensor.electrolux_lavadora_appliancestate') %}
      {% if state == 'Running' %}
        blue
      {% elif state == 'Paused' %}
        orange
      {% elif state == 'End of Cycle' %}
        green
      {% else %}
        disabled
      {% endif %}
    layout: horizontal
    tap_action:
      action: none
    hold_action:
      action: none
    double_tap_action:
      action: none
  - type: custom:gap-card
    height: 15
  - type: heading
    heading: Configurações de Lavagem
    heading_style: title
    icon: mdi:water-sync
    card_mod:
      style: |-
        ha-icon {
          --mdc-icon-size: 30px;
        }
  - type: custom:mushroom-select-card
    entity: input_select.programa_da_lavadora
    name: Programa
    secondary_info: none
  - type: custom:mushroom-select-card
    entity: input_select.nivel_de_agua_da_lavadora
    name: Nível da Água
    secondary_info: none
  - type: custom:gap-card
    height: 15
  - type: heading
    heading: Opções Adicionais
    heading_style: title
    icon: mdi:playlist-plus
    card_mod:
      style: |-
        ha-icon {
          --mdc-icon-size: 30px;
        }
  - type: custom:mushroom-chips-card
    alignment: center
    chips:
      - type: template
        icon: mdi:water-plus
        icon_color: >-
          {{ 'blue' if is_state('input_boolean.lavadora_enxague_extra', 'on')
          else 'disabled' }}
        content: Enxáque Extra
        tap_action:
          action: toggle
        entity: input_boolean.lavadora_enxague_extra
      - type: template
        icon: mdi:waves-arrow-up
        icon_color: >-
          {{ 'blue' if is_state('input_boolean.lavadora_turbo_agitacao', 'on')
          else 'disabled' }}
        content: Turbo Agitação
        tap_action:
          action: toggle
        entity: input_boolean.lavadora_turbo_agitacao
      - type: template
        icon: mdi:turbine
        icon_color: >-
          {{ 'blue' if is_state('input_boolean.lavadora_turbo_centrifugacao',
          'on') else 'disabled' }}
        content: Turbo Centrifugação
        tap_action:
          action: toggle
        entity: input_boolean.lavadora_turbo_centrifugacao
    card_mod:
      style: |-
        ha-card {
          --chip-height: 42px;
          --chip-padding: 0 12px;
          --chip-font-size: 14px;
        }
  - type: custom:gap-card
    height: 15
  - type: heading
    heading: Comandos
    heading_style: title
    icon: mdi:remote
    card_mod:
      style: |-
        ha-icon {
          --mdc-icon-size: 30px;
        }
  - type: grid
    columns: 2
    square: false
    cards:
      - type: custom:mushroom-entity-card
        entity: script.lavadora_acao_inteligente
        name: Iniciar
        secondary_info: none
        icon: mdi:play
        tap_action:
          action: call-service
          service: script.turn_on
          target:
            entity_id: script.lavadora_acao_inteligente
        card_mod:
          style:
            .: |-
              mushroom-shape-icon {
                --icon-color-disabled: rgb(var(--rgb-green));
                --shape-color-disabled: rgba(var(--rgb-green), 0.2);
              }
      - type: custom:mushroom-entity-card
        entity: button.electrolux_lavadora_executecommand_3
        name: Pausar
        secondary_info: none
        icon_color: orange
        tap_action:
          action: call-service
          service: button.press
          target:
            entity_id: button.electrolux_lavadora_executecommand_3
  - type: grid
    columns: 2
    square: false
    cards:
      - type: custom:mushroom-entity-card
        entity: script.lavadora_desligar
        name: Desligar
        secondary_info: none
        icon: mdi:power
        tap_action:
          action: call-service
          service: script.turn_on
          target:
            entity_id: script.lavadora_desligar
        card_mod:
          style:
            .: |-
              mushroom-shape-icon {
                --icon-color-disabled: rgb(var(--rgb-red));
                --shape-color-disabled: rgba(var(--rgb-red), 0.2);
              }
      - type: custom:mushroom-entity-card
        entity: script.lavadora_avancar_etapa
        name: Avançar Etapa
        secondary_info: none
        icon: mdi:skip-next
        tap_action:
          action: call-service
          service: script.turn_on
          target:
            entity_id: script.lavadora_avancar_etapa
```

- **Chips interativos:**  
  - 💧 Enxágue Extra  
  - 🌀 Turbo Agitação  
  - 🏁 Turbo Centrifugação  
- **Comandos rápidos:**  
  - ▶️ Iniciar  
  - ⏸️ Pausar  
  - ⏭️ Avançar Etapa  
  - ⏹️ Desligar

> **Dica:** Segura nos botões pra ações diferentes!  
> Modular, pode customizar à vontade.

## ⚡ Automações

### Controle Central (Programa/Nível d’Água)

Ajusta programa e nível só trocando o select!

```yaml
alias: "Lavadora: Controle Central"
description: Controla a seleção de programa e nível de água com uma única automação
triggers:
  - entity_id: input_select.programa_da_lavadora
    id: programa_mudou
    trigger: state
  - entity_id: input_select.nivel_de_agua_da_lavadora
    id: nivel_agua_mudou
    trigger: state
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: programa_mudou
        sequence:
          - target:
              entity_id: number.electrolux_lavadora_latamuserselections_programid
            data:
              value: >
                {% set mapping = {'Normal':10, 'Pesado/Jeans':1, 'Tira manchas':2, 'Limpeza':5, 'Roupa escura':6, 'Colorida':7, 'Brancas':8, 'Delicado/Esporte':9, 'Rápido':11} %} {{ mapping[trigger.to_state.state] | default(10) }}
            action: number.set_value
      - conditions:
          - condition: trigger
            id: nivel_agua_mudou
        sequence:
          - target:
              entity_id: number.electrolux_lavadora_latamuserselections_washlevel
            data:
              value: >
                {% set mapping = {'Extra baixo':1, 'Extra baixo / baixo':2, 'Baixo':3, 'Baixo / médio':4, 'Médio':5, 'Médio / alto':6, 'Alto':7, 'Alto / Edredom':8, 'Edredom':9} %} {{ mapping[trigger.to_state.state] | default(5) }}
            action: number.set_value
mode: single
```

### Extras (Ligar/Desligar Opções)

Tudo separado pra não dar rolo, ativa/desativa via booleanos:

- **Enxágue Extra**
- **Turbo Agitação**
- **Turbo Centrifugação**

### Enxágue Extra

```yaml
alias: "Lavadora: Controle Enxágue Extra"
description: Ativa ou desativa o enxágue extra
triggers:
  - entity_id:
      - input_boolean.lavadora_enxague_extra
    trigger: state
actions:
  - target:
      entity_id: number.electrolux_lavadora_latamuserselections_rinse
    data:
      value: "{{ 1 if is_state('input_boolean.lavadora_enxague_extra', 'on') else 0 }}"
    action: number.set_value
mode: single
```

### Turbo Agitação

```yaml
alias: "Lavadora: Controle Turbo Agitação"
description: Ativa ou desativa a turbo agitação
triggers:
  - entity_id:
      - input_boolean.lavadora_turbo_agitacao
    trigger: state
actions:
  - target:
      entity_id: number.electrolux_lavadora_latamuserselections_turboagitation
    data:
      value: >-
        {{ 1 if is_state('input_boolean.lavadora_turbo_agitacao', 'on') else 0 }}
    action: number.set_value
mode: single
```

### Turbo Centrifugação

```yaml
alias: "Lavadora: Controle Turbo Centrifugação"
description: Ativa ou desativa a turbo centrifugação
triggers:
  - entity_id:
      - input_boolean.lavadora_turbo_centrifugacao
    trigger: state
actions:
  - target:
      entity_id: number.electrolux_lavadora_latamuserselections_turbodrying
    data:
      value: >-
        {{ 1 if is_state('input_boolean.lavadora_turbo_centrifugacao', 'on') else 0 }}
    action: number.set_value
mode: single
```

## 🤖 Scripts Rápidos

- **Ação Inteligente:** Liga, pausa ou inicia dependendo do estado.
- **Avançar Etapa:** Dá aquele pulo na etapa atual.
- **Desligar:** Força a máquina a desligar, sem dó.

### Ação Inteligente

```yaml
alias: "Lavadora: Ação Inteligente"
sequence:
  - choose:
      - conditions:
          - condition: state
            entity_id: sensor.electrolux_lavadora_appliancestate
            state: Running
        sequence:
          - target:
              entity_id: button.electrolux_lavadora_executecommand_3
            action: button.press
            data: {}
      - conditions:
          - condition: state
            entity_id: sensor.electrolux_lavadora_appliancestate
            state: Paused
        sequence:
          - target:
              entity_id: button.electrolux_lavadora_executecommand_4
            action: button.press
            data: {}
    default:
      - target:
          entity_id: button.electrolux_lavadora_executecommand_2
        action: button.press
        data: {}
      - delay:
          seconds: 2
      - target:
          entity_id: button.electrolux_lavadora_executecommand_5
        action: button.press
        data: {}
mode: single
icon: mdi:play-box-multiple
description: ""
```

### Avançar Etapa

```yaml
alias: "Lavadora: Avançar Etapa"
sequence:
  - target:
      entity_id: button.electrolux_lavadora_executecommand_3
    action: button.press
    data: {}
  - delay:
      seconds: 2
  - target:
      entity_id: number.electrolux_lavadora_latamuserselections_phaseadvance
    data:
      value: "1"
    action: number.set_value
  - delay:
      seconds: 2
  - target:
      entity_id: button.electrolux_lavadora_executecommand_4
    action: button.press
    data: {}
mode: single
icon: mdi:skip-next
description: ""
```

### Desligar

```yaml
alias: "Lavadora: Desligar"
sequence:
  - target:
      entity_id: button.electrolux_lavadora_executecommand
    action: button.press
    data: {}
mode: single
icon: hue:room-laundry-off
description: ""
```

## 🩹 PATCH – Fix do number.py v2.1.0

Corrige o envio do `latamUserSelections`  
Evita de perder configs quando muda só um valor pelo HA.

### Trecho alterado

```python
...
    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        if self.unit == UnitOfTime.SECONDS:
            value = time_minutes_to_seconds(value)
        if self.capability.get("step", 1) == 1:
            value = int(value)
        client: OneAppApi = self.api
        
        # --- START OF OUR FIX ---
        command = {}
        if self.entity_source == "latamUserSelections":
            _LOGGER.debug("Electrolux: Detected latamUserSelections, building full command.")
            # Get the current state of all latam selections
            current_selections = self.appliance_status.get("properties", {}).get("reported", {}).get("latamUserSelections", {})
            if not current_selections:
                _LOGGER.error("Could not retrieve current latamUserSelections to build command.")
                return

            # Create a copy to modify
            new_selections = current_selections.copy()
            # Update only the value we want to change
            new_selections[self.entity_attr] = value
            # Assemble the final command with the entire block
            command = {"latamUserSelections": new_selections}
        # --- END OF OUR FIX ---

        # Original logic as a fallback for other entities
        elif self.entity_source == "userSelections":
            command = {
                self.entity_source: {
                    "programUID": self.appliance_status["properties"]['reported']["userSelections"]['programUID'],
                    self.entity_attr: value
                },
            }
        elif self.entity_source:
            command = {self.entity_source: {self.entity_attr: value}}
        else:
            command = {self.entity_attr: value}

        _LOGGER.debug("Electrolux set value %s", command)
        result = await client.execute_appliance_command(self.pnc_id, command)
        _LOGGER.debug("Electrolux set value result %s", result)
...
```

> **🛠️ ESSENCIAL:** Sempre refaça esse patch se atualizar o HACS do `electrolux_status`!

## 🚨 Observações Ninja

- 📝 Documente qualquer ajuste feito nos scripts/cards!
- 🔄 Patch do `number.py` precisa ser reaplicado quando atualizar a integração!
- 🎛️ Cards mushroom = playground visual, abuse das configs!
- ⏱️ Se os scripts atrasarem ou adiantarem, ajusta os delays.
