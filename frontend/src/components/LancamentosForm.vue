<template>
  <v-card>
    <v-card-title class="text-h5">
      {{ local.id ? "Editar Lançamento" : "Novo Lançamento" }}
    </v-card-title>

    <v-card-text class="pt-4">
      <v-form @submit.prevent="emitSave" :disabled="saving">
        <v-row dense>
          <!-- 1. SELEÇÃO DO TIPO DE PAGAMENTO -->
          <v-col cols="12">
            <label class="v-label mb-1">Forma de Pagamento</label>
            <v-btn-toggle
              v-model="local.paymentMethod"
              color="blue-darken-3"
              variant="outlined"
              divided
              class="w-100"
              :disabled="!!local.id"
            >
              <v-btn value="cash" class="flex-grow-1">
                <v-icon start>mdi-cash</v-icon>
                Pix / Cédula / Débito
              </v-btn>
              <v-btn value="card" class="flex-grow-1">
                <v-icon start>mdi-credit-card</v-icon>
                Cartão de Crédito
              </v-btn>
            </v-btn-toggle>
            <div v-if="local.id" class="text-caption text-disabled mt-1">
              Não é possível alterar a forma de pagamento de um lançamento
              existente.
            </div>
          </v-col>

          <!-- 2. CAMPOS COMUNS -->
          <v-col cols="12">
            <v-text-field
              v-model="local.descricao"
              label="Descrição da Despesa"
              prepend-inner-icon="mdi-text"
              variant="outlined"
              density="compact"
              required
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="local.valor_total"
              label="Valor Total"
              type="number"
              step="0.01"
              prefix="R$"
              prepend-inner-icon="mdi-currency-brl"
              variant="outlined"
              density="compact"
              required
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              :model-value="formatBr(local.competencia)"
              label="Data da Despesa (Competência)"
              prepend-inner-icon="mdi-calendar"
              variant="outlined"
              density="compact"
              readonly
              @click="menus.competencia = true"
              required
            >
              <template #append-inner>
                <v-menu
                  v-model="menus.competencia"
                  :close-on-content-click="false"
                  transition="scale-transition"
                >
                  <template #activator="{ props: menuProps }"
                    ><v-btn v-bind="menuProps" icon size="small" variant="text"
                      ><v-icon>mdi-calendar</v-icon></v-btn
                    ></template
                  >
                  <v-date-picker
                    v-model="local.competencia"
                    @update:modelValue="menus.competencia = false"
                    locale="pt-BR"
                  />
                </v-menu>
              </template>
            </v-text-field>
          </v-col>
          <v-col cols="12" md="6">
            <v-select
              v-model="local.categoria_id"
              :items="categorias"
              item-title="nome"
              item-value="id"
              label="Categoria"
              prepend-inner-icon="mdi-folder-outline"
              variant="outlined"
              density="compact"
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
              variant="outlined"
              density="compact"
              :disabled="!local.categoria_id"
              required
            />
          </v-col>

          <v-col cols="12"><v-divider class="my-2"></v-divider></v-col>

          <!-- 3. CAMPOS CONDICIONAIS PARA CARTÃO DE CRÉDITO -->
          <template v-if="local.paymentMethod === 'card'">
            <v-col cols="12" md="6">
              <v-select
                v-model="local.cartao_id"
                :items="cartoes"
                item-title="nome"
                item-value="id"
                label="Qual cartão foi usado?"
                prepend-inner-icon="mdi-credit-card-outline"
                variant="outlined"
                density="compact"
                required
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model.number="local.parcelas_total"
                label="Total de Parcelas"
                type="number"
                min="1"
                prepend-inner-icon="mdi-format-list-numbered"
                variant="outlined"
                density="compact"
                required
              />
            </v-col>
            <v-col cols="12">
              <v-text-field
                :model-value="formatBr(local.data_vencimento)"
                label="Vencimento da 1ª Parcela"
                prepend-inner-icon="mdi-calendar-alert"
                variant="outlined"
                density="compact"
                readonly
                @click="menus.vencimento = true"
                required
              >
                <template #append-inner>
                  <v-menu
                    v-model="menus.vencimento"
                    :close-on-content-click="false"
                    transition="scale-transition"
                  >
                    <template #activator="{ props: menuProps }"
                      ><v-btn
                        v-bind="menuProps"
                        icon
                        size="small"
                        variant="text"
                        ><v-icon>mdi-calendar</v-icon></v-btn
                      ></template
                    >
                    <v-date-picker
                      v-model="local.data_vencimento"
                      @update:modelValue="menus.vencimento = false"
                      locale="pt-BR"
                    />
                  </v-menu>
                </template>
              </v-text-field>
            </v-col>
          </template>

          <!-- 4. CAMPOS DE DETALHES -->
          <v-col cols="12" md="4">
            <v-select
              v-model="local.escopo"
              :items="escopoOptions"
              item-title="label"
              item-value="value"
              label="Escopo"
              prepend-inner-icon="mdi-account-group-outline"
              variant="outlined"
              density="compact"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-select
              v-model="local.pagador_id"
              :items="membros"
              item-title="label"
              item-value="value"
              label="Quem Pagou?"
              prepend-inner-icon="mdi-account-cash-outline"
              variant="outlined"
              density="compact"
            />
          </v-col>
          <v-col v-if="local.escopo === 'PESS'" cols="12" md="4">
            <v-select
              v-model="local.dono_pessoal_id"
              :items="membros"
              item-title="label"
              item-value="value"
              label="Dono da Despesa"
              prepend-inner-icon="mdi-account-outline"
              variant="outlined"
              density="compact"
            />
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>

    <v-card-actions>
      <v-spacer />
      <v-btn variant="text" @click="$emit('close')">Cancelar</v-btn>
      <v-btn color="blue-darken-3" :loading="saving" @click="emitSave"
        >Salvar</v-btn
      >
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { reactive, watch, computed } from "vue";

const props = defineProps({
  model: { type: Object, default: () => ({}) },
  categorias: { type: Array, default: () => [] },
  subcategorias: { type: Array, default: () => [] },
  membros: { type: Array, default: () => [] },
  statusOptions: { type: Array, default: () => [] },
  escopoOptions: { type: Array, default: () => [] },
  cartoes: { type: Array, default: () => [] },
  saving: { type: Boolean, default: false },
  currentUserId: { type: Number, default: null },
});

const emit = defineEmits(["save", "close"]);

const local = reactive({
  id: null,
  paymentMethod: "cash", // 'cash' ou 'card'
  descricao: "",
  valor_total: "",
  competencia: null,
  data_vencimento: null,
  categoria_id: null,
  subcategoria_id: null,
  cartao_id: null,
  parcelas_total: 1,
  escopo: "COMP",
  pagador_id: null,
  dono_pessoal_id: null,
  status: "PENDENTE", // Adicionado para lançamentos 'cash'
});

const menus = reactive({ competencia: false, vencimento: false });

watch(
  () => [props.model, props.currentUserId],
  ([item, userId]) => {
    const isEditing = item && item.id;

    if (isEditing) {
      // Editando um item existente
      local.id = item.id;
      local.paymentMethod = item.type === "compra" ? "card" : "cash";
      local.descricao = item.descricao;
      local.valor_total = item.valor_total;
      local.competencia = new Date(item.competencia);
      local.data_vencimento = item.data_vencimento
        ? new Date(item.data_vencimento)
        : new Date(item.competencia);
      local.subcategoria_id = item.subcategoria?.id;
      local.categoria_id = item.subcategoria?.categoria?.id;
      local.escopo = item.escopo;
      local.pagador_id = item.pagador_id || item.pagador?.id;
      local.dono_pessoal_id = item.dono_pessoal_id || item.dono_pessoal?.id;
      local.status = item.status || "PENDENTE";

      // Campos de cartão não são editáveis, então ficam zerados
      local.cartao_id = null;
      local.parcelas_total = 1;
    } else {
      // Criando um novo item
      local.id = null;
      local.paymentMethod = "cash";
      local.descricao = "";
      local.valor_total = "";
      local.competencia = new Date();
      local.data_vencimento = new Date();
      local.categoria_id = null;
      local.subcategoria_id = null;
      local.cartao_id = null;
      local.parcelas_total = 1;
      local.escopo = "COMP";
      local.pagador_id = userId;
      local.dono_pessoal_id = null;
      local.status = "PENDENTE";
    }
  },
  { immediate: true, deep: true }
);

watch(
  () => local.escopo,
  (newEscopo) => {
    // Não aplica o padrão se estiver editando, para não sobrescrever
    if (local.id) return;

    if (newEscopo === "PESS") {
      local.dono_pessoal_id = props.currentUserId;
    } else {
      local.dono_pessoal_id = null;
    }
  }
);

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

function onCategoriaChange() {
  const sub = subcategoriasNormalizadas.value.find(
    (s) => s.id === local.subcategoria_id
  );
  if (sub && sub.categoria_id !== local.categoria_id) {
    local.subcategoria_id = null;
  }
}

function toIsoDate(dateValue) {
  if (!dateValue) return null;
  const date = new Date(dateValue);
  if (isNaN(date.getTime())) return null;
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 10);
}

function formatBr(dateValue) {
  if (!dateValue) return "";
  const date = new Date(dateValue);
  if (isNaN(date.getTime())) return "";
  date.setMinutes(date.getMinutes() + date.getTimezoneOffset());
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
}

function emitSave() {
  let finalPayload = {};
  const isCardPurchase = local.paymentMethod === "card" && !local.id;

  if (isCardPurchase) {
    finalPayload = {
      descricao: local.descricao,
      valor_total: local.valor_total,
      subcategoria_id: local.subcategoria_id,
      cartao_id: local.cartao_id,
      parcelas_total: local.parcelas_total,
      primeira_competencia: toIsoDate(local.competencia),
      primeiro_vencimento: toIsoDate(local.data_vencimento),
      escopo: local.escopo,
      pagador_id: local.pagador_id,
      dono_pessoal_id: local.dono_pessoal_id,
      // Passa o 'type' para a view poder decidir o endpoint
      type: "compra",
    };
  } else {
    finalPayload = {
      id: local.id,
      descricao: local.descricao,
      valor_total: local.valor_total,
      subcategoria_id: local.subcategoria_id,
      competencia: toIsoDate(local.competencia),
      data_vencimento: toIsoDate(local.data_vencimento),
      escopo: local.escopo,
      pagador_id: local.pagador_id,
      dono_pessoal_id: local.dono_pessoal_id,
      status: local.status,
      // Passa o 'type' para a view poder decidir o endpoint
      type: "lancamento",
    };
  }

  emit("save", finalPayload);
}
</script>
