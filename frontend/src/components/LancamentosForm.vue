<template>
  <v-card>
    <v-card-title class="text-h5">
      {{ local.id ? "Editar Lançamento" : "Novo Lançamento" }}
    </v-card-title>

    <v-card-text>
      <v-form @submit.prevent="emitSave" :disabled="saving">
        <v-row dense>
          <v-col cols="12" md="6">
            <v-select
              v-model="local.categoria_id"
              :items="categorias"
              item-title="nome"
              item-value="id"
              label="Categoria (grupo)"
              prepend-inner-icon="mdi-folder-outline"
              clearable
              @update:modelValue="onCategoriaChange"
              required
            />
          </v-col>

          <v-col cols="12" md="6">
            <v-select
              v-model="local.subcategoria_id"
              :items="subcategoriasFiltradas"
              item-title="nome"
              item-value="id"
              label="Subcategoria"
              prepend-inner-icon="mdi-shape-outline"
              :disabled="!local.categoria_id"
              required
            />
          </v-col>

          <v-col cols="12" md="6">
            <v-select
              v-model="local.escopo"
              :items="escopoOptions"
              item-title="label"
              item-value="value"
              label="Escopo"
              prepend-inner-icon="mdi-account-multiple-outline"
              required
            />
          </v-col>

          <v-col cols="12" md="6">
            <v-text-field
              v-model="local.valor_total"
              label="Valor total"
              type="number"
              step="0.01"
              prepend-inner-icon="mdi-currency-brl"
              required
            />
          </v-col>

          <v-col cols="12" md="8">
            <v-text-field
              v-model="local.descricao"
              label="Descrição"
              prepend-inner-icon="mdi-text"
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-select
              v-model="local.status"
              :items="statusOptions"
              item-title="label"
              item-value="value"
              label="Status"
              prepend-inner-icon="mdi-flag"
              required
            />
          </v-col>

          <v-col cols="12" md="6">
            <v-text-field
              :model-value="formatBr(local.competencia)"
              :label="
                local.usar_cartao ? 'Competência da 1ª Parcela' : 'Competência'
              "
              hint="Mês a que a despesa se refere"
              persistent-hint
              prepend-inner-icon="mdi-calendar"
              readonly
              @click="menus.competencia = true"
            >
              <template #append-inner>
                <v-menu
                  v-model="menus.competencia"
                  :close-on-content-click="false"
                  transition="scale-transition"
                  offset-y
                >
                  <template #activator="{ props: menuProps }">
                    <v-btn v-bind="menuProps" icon>
                      <v-icon>mdi-calendar</v-icon>
                    </v-btn>
                  </template>
                  <v-date-picker
                    v-model="local.competencia"
                    locale="pt-BR"
                    @update:modelValue="menus.competencia = false"
                  />
                </v-menu>
              </template>
            </v-text-field>
          </v-col>

          <v-col cols="12" md="6">
            <v-text-field
              :model-value="formatBr(local.data_vencimento)"
              :label="
                local.usar_cartao ? 'Vencimento da 1ª Parcela' : 'Vencimento'
              "
              prepend-inner-icon="mdi-calendar-alert"
              readonly
              @click="menus.vencimento = true"
              required
            >
              <template #append-inner>
                <v-menu
                  v-model="menus.vencimento"
                  :close-on-content-click="false"
                  transition="scale-transition"
                  offset-y
                >
                  <template #activator="{ props: menuProps }">
                    <v-btn v-bind="menuProps" icon>
                      <v-icon>mdi-calendar</v-icon>
                    </v-btn>
                  </template>
                  <v-date-picker
                    v-model="local.data_vencimento"
                    locale="pt-BR"
                    @update:modelValue="menus.vencimento = false"
                  />
                </v-menu>
              </template>
            </v-text-field>
          </v-col>

          <v-col cols="12" md="6" v-if="local.escopo === 'PESS'">
            <v-select
              v-model="local.dono_pessoal_id"
              :items="membros"
              item-title="label"
              item-value="value"
              label="Dono (pessoal)"
              prepend-inner-icon="mdi-account"
              required
            />
          </v-col>

          <v-col :cols="12" :md="local.escopo === 'PESS' ? 6 : 12">
            <v-select
              v-model="local.pagador_id"
              :items="membros"
              item-title="label"
              item-value="value"
              label="Pagador"
              prepend-inner-icon="mdi-account-cash"
              required
            />
          </v-col>

          <v-col cols="12">
            <v-switch
              v-model="local.usar_cartao"
              inset
              color="blue-darken-3"
              label="É uma compra parcelada no cartão?"
              :disabled="!!local.id"
              :hint="
                local.id
                  ? 'Opção disponível apenas ao criar um novo lançamento.'
                  : ''
              "
              persistent-hint
            />
          </v-col>

          <v-col cols="12" md="6" v-if="local.usar_cartao">
            <v-select
              v-model="local.cartao_id"
              :items="cartoesLocal"
              item-title="nome"
              item-value="id"
              label="Cartão"
              prepend-inner-icon="mdi-credit-card-outline"
              clearable
            >
              <template #append>
                <v-btn
                  size="small"
                  variant="text"
                  icon
                  @click.stop="showNewCard = !showNewCard"
                  :aria-label="
                    showNewCard ? 'Fechar novo cartão' : 'Novo cartão'
                  "
                >
                  <v-icon>{{ showNewCard ? "mdi-close" : "mdi-plus" }}</v-icon>
                </v-btn>
              </template>
            </v-select>
          </v-col>

          <v-col cols="12" md="6" v-if="local.usar_cartao">
            <v-text-field
              v-model.number="local.parcelas_total"
              label="Total de parcelas"
              type="number"
              min="1"
              prepend-inner-icon="mdi-format-list-numbered"
              required
            />
          </v-col>

          <v-col cols="12" v-if="local.usar_cartao && showNewCard">
            <v-card variant="tonal" class="pa-3">
              <v-row dense>
                <v-col cols="12">
                  <div class="text-subtitle-1">Novo Cartão</div>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="newCard.nome"
                    label="Nome do cartão (Ex: Maria - Nubank)"
                    prepend-inner-icon="mdi-credit-card-plus-outline"
                    :disabled="creatingCard"
                    autofocus
                    required
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="newCard.bandeira"
                    :items="bandeiraOptions"
                    label="Bandeira"
                    prepend-inner-icon="mdi-flag"
                    :disabled="creatingCard"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="newCard.dia_vencimento"
                    label="Dia de vencimento (1–28)"
                    type="number"
                    min="1"
                    max="28"
                    prepend-inner-icon="mdi-calendar-alert"
                    :disabled="creatingCard"
                    required
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="newCard.dia_fechamento"
                    label="Dia de fechamento (1–28)"
                    type="number"
                    min="1"
                    max="28"
                    prepend-inner-icon="mdi-calendar-lock"
                    :disabled="creatingCard"
                    required
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="newCard.limite"
                    label="Limite (opcional)"
                    type="number"
                    step="0.01"
                    prepend-inner-icon="mdi-cash-lock"
                    :disabled="creatingCard"
                  />
                </v-col>

                <v-col cols="12" class="d-flex justify-end">
                  <v-btn
                    variant="text"
                    class="me-2"
                    :disabled="creatingCard"
                    @click="cancelNewCard"
                  >
                    Cancelar
                  </v-btn>
                  <v-btn
                    color="blue-darken-3"
                    :loading="creatingCard"
                    :disabled="
                      !newCard.nome ||
                      !newCard.dia_vencimento ||
                      !newCard.dia_fechamento
                    "
                    @click="createCard"
                  >
                    Salvar cartão
                  </v-btn>
                </v-col>
              </v-row>
            </v-card>
          </v-col>

          <v-col cols="12" md="6" v-if="local.status === 'PAGO'">
            <v-text-field
              :model-value="formatBr(local.data_pagamento)"
              label="Data de pagamento"
              prepend-inner-icon="mdi-calendar-check"
              readonly
              @click="menus.pagamento = true"
            >
              <template #append-inner>
                <v-menu
                  v-model="menus.pagamento"
                  :close-on-content-click="false"
                  transition="scale-transition"
                  offset-y
                >
                  <template #activator="{ props: menuProps }">
                    <v-btn v-bind="menuProps" icon>
                      <v-icon>mdi-calendar</v-icon>
                    </v-btn>
                  </template>
                  <v-date-picker
                    v-model="local.data_pagamento"
                    locale="pt-BR"
                    @update:modelValue="menus.pagamento = false"
                  />
                </v-menu>
              </template>
            </v-text-field>
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>

    <v-card-actions>
      <v-spacer />
      <v-btn variant="text" @click="$emit('close')">Cancelar</v-btn>
      <v-btn color="blue-darken-3" :loading="saving" @click="emitSave">
        Salvar
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { reactive, ref, watch, computed } from "vue";
import axios from "@/api/axios";

const props = defineProps({
  model: { type: Object, default: () => ({}) },
  categorias: { type: Array, default: () => [] },
  subcategorias: { type: Array, default: () => [] },
  membros: { type: Array, default: () => [] },
  statusOptions: { type: Array, default: () => [] },
  escopoOptions: { type: Array, default: () => [] },
  cartoes: { type: Array, default: () => [] },
  saving: { type: Boolean, default: false },
});

const emit = defineEmits(["save", "close"]);

const local = reactive({
  id: null,
  categoria_id: null,
  subcategoria_id: null,
  escopo: "COMP",
  descricao: "",
  valor_total: "",
  competencia: null,
  data_vencimento: null,
  pagador_id: null,
  status: "PENDENTE",
  data_pagamento: null,
  dono_pessoal_id: null,
  usar_cartao: false,
  cartao_id: null,
  parcelas_total: 1,
});

const menus = reactive({
  competencia: false,
  vencimento: false,
  pagamento: false,
});

const cartoesLocal = ref([]);
const showNewCard = ref(false);
const creatingCard = ref(false);
const newCard = reactive({
  nome: "",
  bandeira: "OUTRO",
  limite: null,
  dia_fechamento: 1,
  dia_vencimento: 10,
});
const bandeiraOptions = ["VISA", "MASTER", "ELO", "AMEX", "OUTRO"];

watch(
  () => props.cartoes,
  (arr) => {
    cartoesLocal.value = Array.isArray(arr) ? [...arr] : [];
  },
  { immediate: true }
);

function cancelNewCard() {
  showNewCard.value = false;
  Object.assign(newCard, {
    nome: "",
    bandeira: "OUTRO",
    limite: null,
    dia_fechamento: 1,
    dia_vencimento: 10,
  });
}

async function createCard() {
  if (!newCard.nome || !newCard.dia_vencimento || !newCard.dia_fechamento)
    return;
  creatingCard.value = true;
  try {
    const payload = { ...newCard };
    if (!payload.limite) delete payload.limite;

    const { data } = await axios.post("/cartoes/", payload);
    cartoesLocal.value.push(data);
    local.cartao_id = data.id;
    cancelNewCard();
  } catch (e) {
    console.error("Erro ao criar cartão:", e);
  } finally {
    creatingCard.value = false;
  }
}

const subcategoriasNormalizadas = computed(() =>
  (props.subcategorias || []).map((s) => ({
    ...s,
    categoria_id: s.categoria_id ?? s.categoria?.id ?? null,
  }))
);

const subcategoriasFiltradas = computed(() => {
  if (!local.categoria_id) return [];
  return subcategoriasNormalizadas.value.filter(
    (s) => s.categoria_id === local.categoria_id
  );
});

watch(
  () => props.model,
  (m) => {
    Object.assign(local, {
      id: m?.id ?? null,
      categoria_id: m?.subcategoria?.categoria?.id ?? null,
      subcategoria_id: m?.subcategoria?.id ?? null,
      escopo: m?.escopo ?? "COMP",
      descricao: m?.descricao ?? "",
      valor_total: m?.valor_total ?? "",
      competencia: m?.competencia,
      data_vencimento: m?.data_vencimento,
      pagador_id: m?.pagador?.id ?? null,
      status: m?.status ?? "PENDENTE",
      data_pagamento: m?.data_pagamento ?? null,
      dono_pessoal_id: m?.dono_pessoal?.id ?? null,
      usar_cartao: false,
      cartao_id: null,
      parcelas_total: 1,
    });
    if (!local.categoria_id && m?.subcategoria_id) {
      const sub = subcategoriasNormalizadas.value.find(
        (s) => s.id === m.subcategoria_id
      );
      if (sub) local.categoria_id = sub.categoria_id;
    }
  },
  { immediate: true, deep: true }
);

function onCategoriaChange() {
  const sub = subcategoriasNormalizadas.value.find(
    (s) => s.id === local.subcategoria_id
  );
  if (sub && sub.categoria_id !== local.categoria_id) {
    local.subcategoria_id = null;
  }
}

watch(
  () => local.status,
  (st) => {
    if (st !== "PAGO") local.data_pagamento = null;
  }
);
watch(
  () => local.escopo,
  (esc) => {
    if (esc === "COMP") local.dono_pessoal_id = null;
  }
);
watch(
  () => local.usar_cartao,
  (on) => {
    if (!on) {
      local.cartao_id = null;
      local.parcelas_total = 1;
      showNewCard.value = false;
    }
  }
);

// =================== FUNÇÕES DE DATA CORRIGIDAS ===================
function toIsoDate(dateValue) {
  if (!dateValue) return null;
  const date = new Date(dateValue);
  if (isNaN(date.getTime())) return null;
  // Ajusta para o fuso horário local para garantir que a data não mude
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 10);
}

function formatBr(dateValue) {
  if (!dateValue) return "";
  const date = new Date(dateValue);
  if (isNaN(date.getTime())) return "";

  // Adiciona o offset do fuso horário para exibir a data local correta
  date.setMinutes(date.getMinutes() + date.getTimezoneOffset());

  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
}
// =================================================================

function emitSave() {
  const payload = { ...local };

  delete payload.categoria_id;

  payload.competencia = toIsoDate(payload.competencia);
  payload.data_vencimento = toIsoDate(payload.data_vencimento);
  payload.data_pagamento = toIsoDate(payload.data_pagamento);

  Object.keys(payload).forEach((k) => {
    if (payload[k] === "" || payload[k] === null) delete payload[k];
  });

  emit("save", payload);
}
</script>
