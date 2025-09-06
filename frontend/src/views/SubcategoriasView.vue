<template>
  <v-container fluid>
    <v-card>
      <v-toolbar color="blue-darken-3">
        <v-toolbar-title>Subcategorias</v-toolbar-title>
        <v-spacer />
        <v-btn icon @click="fetchAll"><v-icon>mdi-refresh</v-icon></v-btn>
        <v-btn prepend-icon="mdi-plus" @click="openForm()"
          >Adicionar Subcategoria</v-btn
        >
      </v-toolbar>

      <v-card-text>
        <SubcategoriasList
          :items="subcategorias"
          :loading="loading"
          @edit="openForm"
          @delete="confirmDelete"
        />
      </v-card-text>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="560px">
      <SubcategoriasForm
        :model="edited"
        :categorias="categorias"
        :saving="saving"
        @close="dialog = false"
        @save="save"
      />
    </v-dialog>

    <v-dialog v-model="deleteDialog" persistent max-width="400px">
      <v-card>
        <v-card-title class="text-h5">Confirmar Exclusão</v-card-title>
        <v-card-text
          >Tem certeza que deseja excluir esta subcategoria?</v-card-text
        >
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="deleteDialog = false">Cancelar</v-btn>
          <v-btn color="red-darken-1" @click="removeConfirmed">Excluir</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="errorDialog" persistent max-width="500px">
      <v-card>
        <v-card-title class="text-h5 bg-red-darken-2">
          <v-icon start icon="mdi-alert-circle-outline" />
          Operação Bloqueada
        </v-card-title>
        <v-card-text class="py-4 text-body-1">{{ errorMessage }}</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            color="blue-darken-1"
            variant="elevated"
            @click="errorDialog = false"
            >Entendi</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "@/api/axios";
import SubcategoriasList from "@/components/SubcategoriasList.vue";
import SubcategoriasForm from "@/components/SubcategoriasForm.vue";

const categorias = ref([]);
const subcategorias = ref([]);

const loading = ref(false);
const saving = ref(false);
const dialog = ref(false);
const deleteDialog = ref(false);

const edited = ref({});
const toDelete = ref(null);

const errorDialog = ref(false);
const errorMessage = ref("");

onMounted(fetchAll);

async function fetchAll() {
  loading.value = true;
  try {
    const [cats, subs] = await Promise.all([
      axios.get("/categorias/"),
      axios.get("/subcategorias/"),
    ]);
    categorias.value = cats.data?.results ?? cats.data ?? [];
    subcategorias.value = subs.data?.results ?? subs.data ?? [];
  } catch (e) {
    errorMessage.value = "Não foi possível carregar os dados.";
    errorDialog.value = true;
  } finally {
    loading.value = false;
  }
}

function openForm(item = null) {
  edited.value = item
    ? {
        id: item.id,
        nome: item.nome,
        categoria_id: item.categoria?.id ?? null,
        ativa: !!item.ativa,
      }
    : { id: null, nome: "", categoria_id: null, ativa: true };
  dialog.value = true;
}

async function save(payload) {
  saving.value = true;
  try {
    const body = { ...payload };
    if (body.id) {
      await axios.patch(`/subcategorias/${body.id}/`, body);
    } else {
      await axios.post("/subcategorias/", body);
    }
    dialog.value = false;
    await fetchAll();
  } catch (e) {
    errorMessage.value = "Não foi possível salvar a subcategoria.";
    errorDialog.value = true;
  } finally {
    saving.value = false;
  }
}

function confirmDelete(item) {
  toDelete.value = item;
  deleteDialog.value = true;
}

async function removeConfirmed() {
  try {
    await axios.delete(`/subcategorias/${toDelete.value.id}/`);
    deleteDialog.value = false;
    await fetchAll();
  } catch (e) {
    deleteDialog.value = false;
    errorMessage.value =
      e.response?.data?.detail || "Erro ao excluir subcategoria.";
    errorDialog.value = true;
  }
}
</script>
