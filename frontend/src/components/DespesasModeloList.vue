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

    <!-- valor_previsto -->
    <template #item.valor_previsto="{ item }">
      {{ formatCurrency(item.valor_previsto) }}
    </template>

    <!-- escopo -->
    <template #item.escopo="{ item }">
      <v-chip
        :color="item.escopo === 'COMP' ? 'blue' : 'purple'"
        size="small"
        label
      >
        {{ item.escopo === "COMP" ? "Compartilhada" : "Pessoal" }}
      </v-chip>
    </template>

    <!-- recorrente -->
    <template #item.recorrente="{ item }">
      <v-chip :color="item.recorrente ? 'green' : 'orange'" size="small" label>
        {{ item.recorrente ? "Sim" : "Não" }}
      </v-chip>
    </template>

    <!-- ativo -->
    <template #item.ativo="{ item }">
      <v-chip :color="item.ativo ? 'green' : 'red'" size="small" label>
        {{ item.ativo ? "Ativo" : "Inativo" }}
      </v-chip>
    </template>

    <!-- ações -->
    <template #item.actions="{ item }">
      <v-icon size="small" class="me-2" @click="$emit('edit', item)"
        >mdi-pencil</v-icon
      >
      <v-icon size="small" color="red" @click="$emit('delete', item)"
        >mdi-delete</v-icon
      >
    </template>
  </v-data-table>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
});
defineEmits(["edit", "delete"]);

const headers = [
  { title: "Nome", key: "nome" },
  { title: "Categoria", key: "categoria.nome" },
  { title: "Escopo", key: "escopo" },
  { title: "Valor Previsto", key: "valor_previsto", align: "end" },
  { title: "Dia Venc.", key: "dia_vencimento", align: "center" },
  { title: "Recorrente", key: "recorrente", align: "center" },
  { title: "Periodicidade", key: "periodicidade" },
  { title: "Regra de Rateio", key: "regra_rateio" },
  { title: "Status", key: "ativo" },
  { title: "Ações", key: "actions", sortable: false, align: "end" },
];

function formatCurrency(v) {
  const n = Number(v || 0);
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
</script>
