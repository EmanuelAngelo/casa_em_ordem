<template>
  <v-data-table
    :headers="headers"
    :items="rows"
    :loading="loading"
    item-key="id"
    density="comfortable"
    class="elevation-1"
  >
    <template #item.descricao="{ item }">
      <div class="d-flex align-center">
        <v-icon
          v-if="item.status === 'PAGO'"
          size="18"
          color="green"
          class="me-1"
        >
          {{ iconsLocal.statusPaid }}
        </v-icon>
        <v-icon
          v-else-if="item.status === 'PENDENTE'"
          size="18"
          color="orange"
          class="me-1"
        >
          {{ iconsLocal.statusPending }}
        </v-icon>
        <v-icon v-else size="18" color="grey" class="me-1">
          {{ iconsLocal.statusCanceled }}
        </v-icon>
        <span>{{ item.descricao || "—" }}</span>
      </div>
    </template>

    <template #item.competencia="{ item }">
      <span>{{ fmtMonth(item.competencia) }}</span>
    </template>

    <template #item.data_vencimento="{ item }">
      <span>{{ fmtDate(item.data_vencimento) }}</span>
    </template>

    <template #item.valor_total="{ item }">
      <span class="font-weight-medium">{{
        fmtCurrency(item.valor_total)
      }}</span>
    </template>

    <template #item.status="{ item }">
      <v-chip
        :color="chipColor(item.status)"
        size="small"
        label
        variant="tonal"
      >
        {{ item.status }}
      </v-chip>
    </template>

    <template #item.acoes="{ item }">
      <div class="d-flex justify-end">
        <v-tooltip :text="tooltips.details" v-if="item.__isCard">
          <template #activator="{ props }">
            <span v-bind="props">
              <v-btn
                variant="text"
                density="comfortable"
                size="small"
                class="me-1"
                @click="$emit('view-details', item)"
              >
                <v-icon>{{ iconsLocal.details }}</v-icon>
              </v-btn>
            </span>
          </template>
        </v-tooltip>

        <v-tooltip :text="tooltips.edit">
          <template #activator="{ props }">
            <span v-bind="props">
              <v-btn
                variant="text"
                density="comfortable"
                size="small"
                class="me-1"
                @click="$emit('edit', item)"
              >
                <v-icon>{{ iconsLocal.edit }}</v-icon>
              </v-btn>
            </span>
          </template>
        </v-tooltip>

        <v-tooltip
          :text="item.status === 'PAGO' ? tooltips.alreadyPaid : tooltips.pay"
        >
          <template #activator="{ props }">
            <span v-bind="props">
              <v-btn
                variant="text"
                density="comfortable"
                size="small"
                :disabled="item.status === 'PAGO'"
                @click="$emit('quit', item)"
              >
                <v-icon>{{ iconsLocal.pay }}</v-icon>
              </v-btn>
            </span>
          </template>
        </v-tooltip>
      </div>
    </template>

    <template #no-data>
      <div class="text-center pa-6">Nenhum lançamento encontrado.</div>
    </template>
  </v-data-table>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  items: { type: [Array, Object], default: () => [] },
  loading: { type: Boolean, default: false },
  icons: {
    type: Object,
    default: () => ({
      details: "mdi-eye-outline",
      edit: "mdi-pencil-outline",
      pay: "mdi-cash-check",
      statusPaid: "mdi-check-circle-outline",
      statusPending: "mdi-clock-outline",
      statusCanceled: "mdi-cancel",
    }),
  },
  tooltips: {
    type: Object,
    default: () => ({
      details: "Detalhes / Parcelas",
      edit: "Editar",
      pay: "Quitar",
      alreadyPaid: "Já quitado",
    }),
  },
});

defineEmits(["edit", "quit", "view-details"]);

const iconsLocal = computed(() => ({
  details: props.icons.details || "mdi-eye-outline",
  edit: props.icons.edit || "mdi-pencil-outline",
  pay: props.icons.pay || "mdi-cash-check",
  statusPaid: props.icons.statusPaid || "mdi-check-circle-outline",
  statusPending: props.icons.statusPending || "mdi-clock-outline",
  statusCanceled: props.icons.statusCanceled || "mdi-cancel",
}));

const headers = [
  { title: "Descrição", key: "descricao", align: "start" },
  { title: "Competência", key: "competencia", align: "start" },
  { title: "Vencimento", key: "data_vencimento", align: "start" },
  { title: "Valor", key: "valor_total", align: "end" },
  { title: "Status", key: "status", align: "start" },
  { title: "Ações", key: "acoes", align: "end", sortable: false },
];

const rows = computed(() => {
  const list = Array.isArray(props.items)
    ? props.items
    : props.items?.results ?? [];

  return (list || []).map((i, idx) => {
    const isCard =
      i?.type === "compra" ||
      !!i?.compra_cartao ||
      !!i?.compra_cartao_id ||
      !!i?.parcelas_total ||
      !!i?.parcela_numero;

    return {
      id: i.id ?? idx,
      descricao: i.descricao ?? "",
      valor_total: toNumber(i.valor_total),
      status: i.status ?? "PENDENTE",
      competencia: i.competencia ?? null,
      data_vencimento: i.data_vencimento ?? null,
      __isCard: isCard,
      raw: i,
    };
  });
});

function toNumber(v) {
  if (v === null || v === undefined) return 0;
  const n = typeof v === "string" ? Number(v.replace(",", ".")) : Number(v);
  return isNaN(n) ? 0 : n;
}

function fmtCurrency(v) {
  return toNumber(v).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

function fmtDate(v) {
  if (!v) return "—";
  try {
    const d = typeof v === "string" ? new Date(v) : v;
    return d.toLocaleDateString("pt-BR");
  } catch {
    return v;
  }
}

function fmtMonth(v) {
  if (!v) return "—";
  try {
    const d = typeof v === "string" ? new Date(v) : v;
    return d.toLocaleDateString("pt-BR", { month: "2-digit", year: "numeric" });
  } catch {
    if (typeof v === "string" && /^\d{4}-\d{2}/.test(v)) {
      const [y, m] = v.split("-");
      return `${m}/${y}`;
    }
    return v;
  }
}

function chipColor(status) {
  if (status === "PAGO") return "green";
  if (status === "PENDENTE") return "orange";
  if (status === "CANCELADO") return "grey";
  return "blue";
}
</script>
