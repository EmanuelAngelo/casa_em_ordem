<template>
  <v-data-table
    :headers="headers"
    :items="items"
    :loading="loading"
    class="elevation-1"
    item-value="id"
    density="compact"
  >
    <!-- Loading -->
    <template #loading>
      <v-skeleton-loader type="table-row@5" />
    </template>

    <!-- Descrição (sem mudanças) -->
    <template #item.descricao="{ item }">
      {{ item.descricao }}
    </template>

    <!-- Categoria (segura aninhado) -->
    <template #item["categoria.nome"]="{ item }">
      {{ item.categoria?.nome || "-" }}
    </template>

    <!-- Competência -->
    <template #item.competencia="{ item }">
      {{ formatDate(item.competencia) }}
    </template>

    <!-- Vencimento -->
    <template #item.data_vencimento="{ item }">
      {{ formatDate(item.data_vencimento) }}
    </template>

    <!-- Parc. (mostra 2/10, por ex.) -->
    <template #item.parcela="{ item }">
      <span v-if="parcelasTotal(item)">
        {{ parcelaAtual(item) }}/{{ parcelasTotal(item) }}
      </span>
      <span v-else>-</span>
    </template>

    <!-- Valor -->
    <template #item.valor_total="{ item }">
      {{ formatCurrency(item.valor_total) }}
    </template>

    <!-- Escopo -->
    <template #item.escopo="{ item }">
      <v-chip
        :color="item.escopo === 'COMP' ? 'blue' : 'purple'"
        size="small"
        label
      >
        {{ item.escopo === "COMP" ? "Compartilhada" : "Pessoal" }}
      </v-chip>
    </template>

    <!-- Status -->
    <template #item.status="{ item }">
      <v-chip :color="statusColor(item.status)" size="small" label>
        {{ statusLabel(item.status) }}
      </v-chip>
    </template>

    <!-- Ações -->
    <template #item.actions="{ item }">
      <v-icon size="small" class="me-2" @click="$emit('edit', item)">
        mdi-pencil
      </v-icon>
      <v-icon
        size="small"
        class="me-2"
        color="green"
        v-if="item.status !== 'PAGO'"
        @click="$emit('quit', item)"
      >
        mdi-check-decagram
      </v-icon>
      <v-icon size="small" color="red" @click="$emit('delete', item)">
        mdi-delete
      </v-icon>
    </template>
  </v-data-table>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
});

defineEmits(["edit", "delete", "quit"]);

/** Ordem de colunas: coloquei “Parc.” antes de Valor/Status para dar mais destaque */
const headers = [
  { title: "Descrição", key: "descricao" },
  { title: "Categoria", key: "categoria.nome" },
  { title: "Escopo", key: "escopo" },
  { title: "Competência", key: "competencia" },
  { title: "Vencimento", key: "data_vencimento" },
  // { title: "Parc.", key: "parcela", align: "center", sortable: false },
  { title: "Valor", key: "valor_total", align: "end" },
  { title: "Status", key: "status" },
  { title: "Ações", key: "actions", sortable: false, align: "end" },
];

const statusOptions = [
  { label: "Pendente", value: "PENDENTE" },
  { label: "Pago", value: "PAGO" },
  { label: "Cancelado", value: "CANCELADO" },
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
    default:
      return "orange";
  }
}

function formatCurrency(v) {
  const n = Number(v || 0);
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("pt-BR", { timeZone: "UTC" });
}

/** Suporta ambos os nomes vindos do backend:
 *  - parcela_atual/parcela_numero
 *  - parcelas_total
 */
function parcelaAtual(item) {
  return item.parcela_atual ?? item.parcela_numero ?? null;
}
function parcelasTotal(item) {
  return item.parcelas_total ?? null;
}
</script>
