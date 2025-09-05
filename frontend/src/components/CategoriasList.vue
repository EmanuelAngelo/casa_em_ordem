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

    <template #item.ativa="{ item }">
      <v-chip :color="item.ativa ? 'green' : 'red'" size="small" label>
        {{ item.ativa ? "Ativa" : "Inativa" }}
      </v-chip>
    </template>

    <template #item.actions="{ item }">
      <v-icon size="small" class="me-2" @click="$emit('edit', item)">
        mdi-pencil
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
defineEmits(["edit", "delete"]);

const headers = [
  { title: "Nome", key: "nome" },
  { title: "Status", key: "ativa" },
  { title: "Ações", key: "actions", sortable: false, align: "end" },
];
</script>
