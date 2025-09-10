<template>
  <v-data-table
    :headers="headers"
    :items="items"
    :loading="loading"
    class="elevation-1"
    item-value="id"
    density="compact"
  >
    <template #loading>
      <v-skeleton-loader type="table-row@5" />
    </template>

    <template #item.descricao="{ item }">
      <v-icon v-if="item.type === 'compra'" start size="small" color="grey"
        >mdi-credit-card-multiple-outline</v-icon
      >
      <v-icon v-else start size="small" color="grey">mdi-cash</v-icon>
      {{ item.descricao }}
    </template>

    <template #item.competencia="{ item }">
      {{ formatDate(item.competencia) }}
    </template>

    <template #item.parcelas_total="{ item }">
      <v-chip v-if="item.parcelas_total > 1" size="small" label>
        {{ item.parcelas_total }}x
      </v-chip>
      <span v-else>Única</span>
    </template>

    <template #item.valor_total="{ item }">
      <span class="font-weight-bold">{{
        formatCurrency(item.valor_total)
      }}</span>
    </template>

    <template #item.status="{ item }">
      <v-chip :color="statusColor(item.status)" size="small" label>
        {{ statusLabel(item.status) }}
      </v-chip>
    </template>

    <template #item.actions="{ item }">
      <!-- Botão de detalhes SÓ para compras parceladas -->
      <v-icon
        v-if="item.type === 'compra'"
        size="small"
        class="me-2"
        color="blue-darken-2"
        @click="$emit('view-details', item)"
        title="Ver Parcelas"
      >
        mdi-playlist-check
      </v-icon>

      <!-- Ações padrão (editar, quitar, excluir) SÓ para lançamentos únicos -->
      <template v-if="item.type === 'lancamento'">
        <v-icon
          size="small"
          class="me-2"
          @click="$emit('edit', item)"
          title="Editar"
          >mdi-pencil</v-icon
        >
        <v-icon
          v-if="item.status !== 'PAGO'"
          size="small"
          class="me-2"
          color="green"
          @click="$emit('quit', item)"
          title="Quitar"
        >
          mdi-check-decagram
        </v-icon>
        <!-- A deleção de compras parceladas deve ser tratada com mais cuidado, por isso não está aqui -->
      </template>
    </template>
  </v-data-table>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
});

defineEmits(["edit", "quit", "view-details"]);

const headers = [
  { title: "Descrição", key: "descricao", minWidth: "250px" },
  { title: "Categoria", key: "subcategoria.categoria.nome" },
  { title: "Competência", key: "competencia" },
  { title: "Parcelas", key: "parcelas_total", align: "center" },
  { title: "Valor Total", key: "valor_total", align: "end" },
  { title: "Status", key: "status", align: "center" },
  {
    title: "Ações",
    key: "actions",
    sortable: false,
    align: "end",
    width: "120px",
  },
];

const statusOptions = [
  { label: "Pendente", value: "PENDENTE" },
  { label: "Pago", value: "PAGO" },
  { label: "Cancelado", value: "CANCELADO" },
  { label: "Parcelada", value: "PARCELADA" },
];

function statusLabel(s) {
  return statusOptions.find((o) => o.value === s)?.label || s;
}
function statusColor(s) {
  switch (s) {
    case "PAGO":
      return "green";
    case "CANCELADO":
      return "red";
    case "PARCELADA":
      return "blue";
    default:
      return "orange";
  }
}

function formatCurrency(v) {
  return Number(v || 0).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

function formatDate(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  if (isNaN(date.getTime())) return "";
  date.setMinutes(date.getMinutes() + date.getTimezoneOffset());
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
}
</script>
