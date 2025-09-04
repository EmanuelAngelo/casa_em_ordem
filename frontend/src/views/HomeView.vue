<template>
  <v-container fluid>
    <v-card>
      <v-toolbar color="blue-darken-3">
        <v-toolbar-title>Dashboard</v-toolbar-title>
        <v-spacer />
        <v-btn icon @click="refresh"><v-icon>mdi-refresh</v-icon></v-btn>
      </v-toolbar>
      <v-card-text>
        <div class="text-body-1">
          Bem-vindo! Em breve, resumo do mês e vencimentos.
        </div>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
const refresh = () => window.location.reload();
</script>
