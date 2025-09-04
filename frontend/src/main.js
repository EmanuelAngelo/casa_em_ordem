import { createApp } from "vue";
import App from "./App.vue";
import installPlugins from "@/plugins";

import "@mdi/font/css/materialdesignicons.css";
import "@/styles/settings.scss";

const app = createApp(App);
installPlugins(app);
app.mount("#app");
