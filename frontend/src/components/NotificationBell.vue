<template>
  <div class="notification-bell">
    <button class="bell-button" @click="togglePanel" ref="bellBtn">
      <i class="pi pi-bell" :class="{ 'p-overlay-badge': unreadCount > 0 }">
        <span v-if="unreadCount > 0" class="p-badge p-badge-danger">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
      </i>
    </button>

    <OverlayPanel ref="overlayPanel" :showCloseIcon="false" class="notification-panel" @hide="panelVisible = false">
      <template #default>
        <div class="panel-header">
          <h3>Notificaciones</h3>
          <Button v-if="unreadCount > 0" label="Marcar todas" icon="pi pi-check" text size="small" @click="handleMarkAllRead" />
        </div>

        <div class="panel-content" v-if="loading">
          <ProgressSpinner style="width: 40px; height: 40px;" />
        </div>

        <div class="panel-content" v-else-if="notifications.length === 0">
          <div class="empty-state">
            <i class="pi pi-inbox"></i>
            <p>No hay notificaciones</p>
          </div>
        </div>

        <div class="panel-content" v-else>
          <div
            v-for="notif in notifications"
            :key="notif.id"
            class="notification-item"
            :class="{ unread: !notif.is_read }"
            @click="handleClickNotification(notif)"
          >
            <div class="notification-icon" :class="getTypeClass(notif.notification_type)">
              <i :class="getTypeIcon(notif.notification_type)"></i>
            </div>
            <div class="notification-body">
              <p class="notification-title">{{ notif.title }}</p>
              <p class="notification-message">{{ notif.message }}</p>
              <span class="notification-time">{{ formatTime(notif.created_at) }}</span>
            </div>
          </div>
        </div>
      </template>
    </OverlayPanel>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import OverlayPanel from 'primevue/overlaypanel';
import Button from 'primevue/button';
import ProgressSpinner from 'primevue/progressspinner';
import { notificationService } from '@/services/api';

const router = useRouter();
const overlayPanel = ref();
const bellBtn = ref();
const notifications = ref([]);
const unreadCount = ref(0);
const loading = ref(false);
const panelVisible = ref(false);
let pollInterval = null;

const togglePanel = async (event) => {
  panelVisible.value = !panelVisible.value;
  overlayPanel.value.toggle(event);
  if (panelVisible.value) {
    await fetchNotifications();
  }
};

const fetchNotifications = async () => {
  loading.value = true;
  try {
    const [notifRes, countRes] = await Promise.all([
      notificationService.getAll(false),
      notificationService.getCount(),
    ]);
    notifications.value = notifRes.data.slice(0, 20);
    unreadCount.value = countRes.data.unread;
  } catch (error) {
    console.error('Error fetching notifications:', error);
  } finally {
    loading.value = false;
  }
};

const fetchCount = async () => {
  try {
    const res = await notificationService.getCount();
    unreadCount.value = res.data.unread;
  } catch {
    // silent
  }
};

const handleMarkAllRead = async () => {
  try {
    await notificationService.markAllRead();
    notifications.value.forEach(n => { n.is_read = true; });
    unreadCount.value = 0;
  } catch (error) {
    console.error('Error marking all read:', error);
  }
};

const handleClickNotification = async (notif) => {
  if (!notif.is_read) {
    try {
      await notificationService.markRead(notif.id);
      notif.is_read = true;
      unreadCount.value = Math.max(0, unreadCount.value - 1);
    } catch {
      // silent
    }
  }
  overlayPanel.value.hide();
  if (notif.link) {
    router.push(notif.link);
  }
};

const getTypeIcon = (type) => {
  const icons = {
    STATE_CHANGE: 'pi pi-sync',
    STATE_EXPIRING: 'pi pi-exclamation-triangle',
    ASSIGNMENT: 'pi pi-user-plus',
    AGREEMENT: 'pi pi-handshake',
    INSTALLMENT_DUE: 'pi pi-calendar-clock',
    GENERAL: 'pi pi-info-circle',
  };
  return icons[type] || 'pi pi-info-circle';
};

const getTypeClass = (type) => {
  const classes = {
    STATE_CHANGE: 'type-info',
    STATE_EXPIRING: 'type-warning',
    ASSIGNMENT: 'type-success',
    AGREEMENT: 'type-primary',
    INSTALLMENT_DUE: 'type-warning',
    GENERAL: 'type-default',
  };
  return classes[type] || 'type-default';
};

const formatTime = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now - date;
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return 'Ahora';
  if (minutes < 60) return `Hace ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `Hace ${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `Hace ${days}d`;
  return date.toLocaleDateString();
};

onMounted(() => {
  fetchCount();
  pollInterval = setInterval(fetchCount, 60000); // Poll every 60s
});

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval);
});
</script>

<style scoped>
.notification-bell {
  position: relative;
}

.bell-button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  color: #6c757d;
  padding: 8px;
  border-radius: 50%;
  transition: background-color 0.2s;
  position: relative;
}

.bell-button:hover {
  background-color: #f0f0f0;
}

.p-overlay-badge {
  position: relative;
}

.p-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  font-size: 0.65rem;
  min-width: 16px;
  height: 16px;
  line-height: 16px;
  border-radius: 50%;
  padding: 0 4px;
}

.p-badge-danger {
  background-color: #ef4444;
  color: white;
}

.notification-panel {
  width: 380px;
  max-height: 500px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid #e9ecef;
  margin-bottom: 8px;
}

.panel-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #333;
}

.panel-content {
  max-height: 400px;
  overflow-y: auto;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.empty-state i {
  font-size: 2rem;
  margin-bottom: 8px;
  display: block;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.15s;
  gap: 10px;
}

.notification-item:hover {
  background-color: #f8f9fa;
}

.notification-item.unread {
  background-color: #f0f7ff;
}

.notification-item.unread:hover {
  background-color: #e6f0fa;
}

.notification-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.85rem;
}

.type-default { background: #e9ecef; color: #6c757d; }
.type-info { background: #dbeafe; color: #2563eb; }
.type-warning { background: #fef3c7; color: #d97706; }
.type-success { background: #d1fae5; color: #059669; }
.type-primary { background: #e0e7ff; color: #4f46e5; }

.notification-body {
  flex: 1;
  min-width: 0;
}

.notification-title {
  margin: 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #333;
}

.notification-message {
  margin: 2px 0 0;
  font-size: 0.8rem;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-time {
  font-size: 0.7rem;
  color: #999;
}
</style>
