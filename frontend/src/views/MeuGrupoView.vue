<template>
  <v-container fluid>
    <v-card>
      <v-toolbar color="blue-darken-3">
        <v-toolbar-title>Meu Grupo</v-toolbar-title>
        <v-spacer />

        <!-- Botão só aparece quando NÃO há grupo -->
        <v-btn
          v-if="!hasGrupo"
          prepend-icon="mdi-account-multiple-plus"
          @click="createDialog = true"
        >
          Criar Grupo
        </v-btn>

        <v-btn prepend-icon="mdi-lock" @click="passwordDialog = true">
          Alterar Senha
        </v-btn>
        <v-btn icon @click="loadGrupo" :disabled="saving || loading">
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
      </v-toolbar>

      <v-card-text>
        <v-skeleton-loader v-if="loading" type="article, actions" />

        <!-- Estado: já tem grupo -->
        <v-row v-else-if="grupo">
          <v-col cols="12" md="6">
            <v-text-field
              v-model="grupo.nome"
              label="Nome do Grupo"
              variant="outlined"
              density="compact"
              class="mb-4"
            />
            <v-list-subheader>Moradores e Salários</v-list-subheader>
            <div v-for="m in grupo.membros" :key="m.id" class="mb-3">
              <v-text-field
                v-model.number="m.salario_mensal"
                :label="`Salário de ${
                  m.usuario.first_name || m.usuario.username
                }`"
                type="number"
                step="0.01"
                prefix="R$"
                density="compact"
                variant="outlined"
                hide-details
              />
            </div>
            <v-btn
              color="blue-darken-3"
              :loading="saving"
              @click="saveMoradores"
              class="mt-2"
            >
              Salvar Alterações
            </v-btn>
          </v-col>

          <v-col cols="12" md="6">
            <v-card variant="outlined" class="fill-height">
              <v-card-title>Adicionar morador</v-card-title>
              <v-card-subtitle
                >Adicione um usuário já cadastrado</v-card-subtitle
              >
              <v-card-text>
                <v-form @submit.prevent="onInvite" :disabled="loadingInvite">
                  <v-text-field
                    v-model="usernameOrEmail"
                    label="Username ou e-mail"
                    prepend-inner-icon="mdi-account-plus"
                    required
                  />
                  <v-btn
                    color="blue-darken-3"
                    :loading="loadingInvite"
                    type="submit"
                  >
                    Adicionar
                  </v-btn>
                  <v-alert
                    v-if="inviteMsg"
                    class="mt-4"
                    :type="inviteType"
                    variant="tonal"
                  >
                    {{ inviteMsg }}
                  </v-alert>
                </v-form>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Estado: não tem grupo -->
        <v-alert v-else type="info" variant="tonal" class="pa-4 text-center">
          <h3 class="text-h6">Você ainda não tem um grupo.</h3>
          <p class="mt-2">
            Crie um grupo agora para começar a organizar as finanças da casa.
          </p>
          <v-btn
            v-if="!hasGrupo"
            color="blue-darken-3"
            class="mt-2"
            @click="createDialog = true"
          >
            Criar Grupo
          </v-btn>
        </v-alert>
      </v-card-text>
    </v-card>

    <!-- Criar Grupo -->
    <v-dialog v-model="createDialog" persistent max-width="480px">
      <v-card>
        <v-card-title>Criar novo grupo</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="novoGrupoNome"
            label="Nome do grupo"
            prepend-inner-icon="mdi-home-group"
            autofocus
            required
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="createDialog = false">Cancelar</v-btn>
          <v-btn color="blue-darken-3" :loading="creating" @click="createGrupo"
            >Criar</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Alterar senha -->
    <v-dialog v-model="passwordDialog" persistent max-width="500px">
      <v-card>
        <v-card-title><span class="text-h5">Alterar Senha</span></v-card-title>
        <v-card-text>
          <v-form @submit.prevent="changePassword" :disabled="savingPassword">
            <v-text-field
              v-model="passwordForm.nova_senha"
              label="Nova Senha"
              type="password"
              prepend-inner-icon="mdi-lock"
              class="mb-2"
              :error-messages="passwordErrors.nova_senha"
              required
            />
            <v-text-field
              v-model="passwordForm.confirmacao_senha"
              label="Confirmar Nova Senha"
              type="password"
              prepend-inner-icon="mdi-lock-check"
              :error-messages="passwordErrors.confirmacao_senha"
              required
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="passwordDialog = false">Cancelar</v-btn>
          <v-btn
            variant="text"
            color="blue-darken-1"
            :loading="savingPassword"
            @click="changePassword"
          >
            Salvar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="4000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from "vue";
import axios from "@/api/axios";

const grupo = ref(null);
const loading = ref(true);
const saving = ref(false);
const loadingInvite = ref(false);
const usernameOrEmail = ref("");
const inviteMsg = ref("");
const inviteType = ref("info");

const createDialog = ref(false);
const novoGrupoNome = ref("");
const creating = ref(false);

const snackbar = reactive({ show: false, text: "", color: "success" });

// senha
const passwordDialog = ref(false);
const savingPassword = ref(false);
const passwordForm = reactive({ nova_senha: "", confirmacao_senha: "" });
const passwordErrors = ref({});

// computed para facilitar o controle do botão
const hasGrupo = computed(() => !!grupo.value);

onMounted(loadGrupo);

async function loadGrupo() {
  loading.value = true;
  try {
    // /grupos/meu/ retorna 200 com null quando não há grupo
    const { data } = await axios.get("/grupos/meu/");
    grupo.value = data;
  } catch (e) {
    grupo.value = null;
    console.error("Não foi possível carregar dados do grupo:", e);
  } finally {
    loading.value = false;
  }
}

async function createGrupo() {
  if (!novoGrupoNome.value?.trim()) {
    snackbar.show = true;
    snackbar.text = "Informe um nome para o grupo.";
    snackbar.color = "error";
    return;
  }
  creating.value = true;
  try {
    const { data } = await axios.post("/grupos/", {
      nome: novoGrupoNome.value.trim(),
    });
    snackbar.show = true;
    snackbar.text = "Grupo criado com sucesso!";
    snackbar.color = "success";
    createDialog.value = false;
    novoGrupoNome.value = "";
    await loadGrupo(); // ao carregar, hasGrupo fica true e o botão some
  } catch (e) {
    snackbar.show = true;
    snackbar.text =
      e.response?.data?.detail || "Não foi possível criar o grupo.";
    snackbar.color = "error";
  } finally {
    creating.value = false;
  }
}

async function saveMoradores() {
  if (!grupo.value?.id) {
    snackbar.show = true;
    snackbar.text = "Grupo não encontrado.";
    snackbar.color = "error";
    return;
  }
  saving.value = true;
  try {
    await axios.patch(`/grupos/${grupo.value.id}/`, { nome: grupo.value.nome });
    const promises = (grupo.value.membros || []).map((m) =>
      axios.patch(`/moradores/${m.id}/`, {
        salario_mensal: m.salario_mensal || 0,
      })
    );
    await Promise.all(promises);
    snackbar.show = true;
    snackbar.text = "Dados do grupo salvos!";
    snackbar.color = "success";
  } catch (e) {
    snackbar.show = true;
    snackbar.text = e.response?.data?.detail || "Erro ao salvar dados.";
    snackbar.color = "error";
  } finally {
    saving.value = false;
  }
}

async function onInvite() {
  inviteMsg.value = "";
  inviteType.value = "info";
  loadingInvite.value = true;
  try {
    const { data } = await axios.post("/grupos-extras/convidar/", {
      username_or_email: usernameOrEmail.value,
    });
    inviteMsg.value = data.detail || "Usuário adicionado ao grupo.";
    inviteType.value = "success";
    usernameOrEmail.value = "";
    await loadGrupo();
  } catch (e) {
    inviteMsg.value =
      e.response?.data?.detail || "Não foi possível adicionar o usuário.";
    inviteType.value = "error";
  } finally {
    loadingInvite.value = false;
  }
}

async function changePassword() {
  savingPassword.value = true;
  passwordErrors.value = {};
  try {
    const { data } = await axios.post("/auth/change-password/", passwordForm);
    snackbar.show = true;
    snackbar.text = data.detail || "Senha alterada!";
    snackbar.color = "success";
    passwordForm.nova_senha = "";
    passwordForm.confirmacao_senha = "";
    passwordDialog.value = false;
  } catch (e) {
    const errors = e.response?.data;
    if (errors && typeof errors === "object") {
      const firstErrorKey = Object.keys(errors)[0];
      const errorMessages = errors[firstErrorKey];
      const detail = Array.isArray(errorMessages)
        ? errorMessages[0]
        : errorMessages;
      snackbar.show = true;
      snackbar.text = detail || "Não foi possível alterar a senha.";
      snackbar.color = "error";
      passwordErrors.value = errors;
    } else {
      snackbar.show = true;
      snackbar.text = "Não foi possível alterar a senha.";
      snackbar.color = "error";
    }
  } finally {
    savingPassword.value = false;
  }
}
</script>
