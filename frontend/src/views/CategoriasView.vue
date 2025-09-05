<template>
  <v-container fluid>
    <v-card>
      <v-toolbar color="blue-darken-3">
        <v-toolbar-title>Categorias</v-toolbar-title>
        <v-spacer />
        <v-btn icon @click="fetchCategorias">
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
        <v-btn prepend-icon="mdi-plus" @click="openForm()">
          Adicionar Categoria
        </v-btn>
      </v-toolbar>

      <v-card-text>
        <CategoriasList
          :items="categorias"
          :loading="loading"
          @edit="openForm"
          @delete="confirmDelete"
        />
      </v-card-text>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="520px">
      <CategoriasForm
        :model="editedCategoria"
        :saving="saving"
        @close="dialog = false"
        @save="saveCategoria"
      />
    </v-dialog>

    <v-dialog v-model="deleteDialog" persistent max-width="400px">
      <v-card>
        <v-card-title class="text-h5">Confirmar Exclusão</v-card-title>
        <v-card-text
          >Tem certeza que deseja excluir esta categoria?</v-card-text
        >
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="deleteDialog = false">Cancelar</v-btn>
          <v-btn color="red-darken-1" @click="deleteCategoriaConfirmed"
            >Excluir</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="errorDialog" persistent max-width="500px">
      <v-card>
        <v-card-title class="text-h5 bg-red-darken-2">
          <v-icon start icon="mdi-alert-circle-outline" />
          Operação Bloqueada
        </v-card-title>
        <v-card-text class="py-4 text-body-1">
          {{ errorMessage }}
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            color="blue-darken-1"
            variant="elevated"
            @click="errorDialog = false"
          >
            Entendi
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "@/api/axios";
import CategoriasList from "@/components/CategoriasList.vue";
import CategoriasForm from "@/components/CategoriasForm.vue";

const categorias = ref([]);
const loading = ref(false);
const saving = ref(false);
const dialog = ref(false);
const deleteDialog = ref(false);

const editedCategoria = ref({});
const categoriaToDelete = ref(null);

const errorDialog = ref(false);
const errorMessage = ref("");

const defaultCategoria = {
  nome: "",
  ativa: true,
};

onMounted(fetchCategorias);

async function fetchCategorias() {
  loading.value = true;
  try {
    const resp = await axios.get("/categorias/");
    categorias.value = resp.data?.results ?? resp.data ?? [];
  } catch (e) {
    errorMessage.value = "Não foi possível carregar as categorias.";
    errorDialog.value = true;
  } finally {
    loading.value = false;
  }
}

function openForm(item = null) {
  editedCategoria.value = item
    ? { id: item.id, nome: item.nome, ativa: !!item.ativa }
    : { ...defaultCategoria };
  dialog.value = true;
}

async function saveCategoria(payload) {
  saving.value = true;
  try {
    const body = {
      id: payload.id ?? undefined,
      nome: payload.nome,
      ativa: !!payload.ativa,
    };
    if (body.id) {
      await axios.patch(`/categorias/${body.id}/`, body);
    } else {
      await axios.post("/categorias/", body);
    }
    dialog.value = false;
    await fetchCategorias();
  } catch (e) {
    errorMessage.value = "Não foi possível salvar a categoria.";
    errorDialog.value = true;
  } finally {
    saving.value = false;
  }
}

function confirmDelete(item) {
  categoriaToDelete.value = item;
  deleteDialog.value = true;
}

async function deleteCategoriaConfirmed() {
  try {
    await axios.delete(`/categorias/${categoriaToDelete.value.id}/`);
    deleteDialog.value = false;
    await fetchCategorias();
  } catch (e) {
    deleteDialog.value = false;
    errorMessage.value =
      e.response?.data?.detail || "Ocorreu um erro ao excluir a categoria.";
    errorDialog.value = true;
  }
}
</script>
