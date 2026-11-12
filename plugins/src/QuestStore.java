package fr.citadelle.messages;

import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.plugin.Plugin;

import java.io.File;
import java.io.IOException;
import java.util.UUID;

/**
 * Player quest progress in quetes.yml: players.<uuid>.<jour|semaine>.{id, progres.<quest>, faites.<quest>, bonus}
 * and players.<uuid>.total. A period whose id changed (new day / week) is wiped on first access.
 */
final class QuestStore {

    private final Plugin plugin;
    private final File file;
    private final YamlConfiguration data;
    private boolean dirty;

    QuestStore(Plugin plugin) {
        this.plugin = plugin;
        this.file = new File(plugin.getDataFolder(), "quetes.yml");
        this.data = YamlConfiguration.loadConfiguration(file);
    }

    private String base(UUID id, Quest.Period period, String periodId) {
        String b = "players." + id + "." + period.name().toLowerCase(java.util.Locale.ROOT);
        if (!periodId.equals(data.getString(b + ".id"))) {
            data.set(b, null);
            data.set(b + ".id", periodId);
            dirty = true;
        }
        return b;
    }

    int progress(UUID id, Quest q, String periodId) {
        return data.getInt(base(id, q.period(), periodId) + ".progres." + q.id());
    }

    int add(UUID id, Quest q, String periodId, int amount) {
        String key = base(id, q.period(), periodId) + ".progres." + q.id();
        int v = Math.min(q.amount(), data.getInt(key) + amount);
        data.set(key, v);
        dirty = true;
        return v;
    }

    boolean done(UUID id, Quest q, String periodId) {
        return data.getBoolean(base(id, q.period(), periodId) + ".faites." + q.id());
    }

    void markDone(UUID id, Quest q, String periodId) {
        data.set(base(id, q.period(), periodId) + ".faites." + q.id(), true);
        data.set("players." + id + ".total", total(id) + 1);
        dirty = true;
    }

    boolean bonus(UUID id, Quest.Period period, String periodId) {
        return data.getBoolean(base(id, period, periodId) + ".bonus");
    }

    void markBonus(UUID id, Quest.Period period, String periodId) {
        data.set(base(id, period, periodId) + ".bonus", true);
        dirty = true;
    }

    int total(UUID id) {
        return data.getInt("players." + id + ".total");
    }

    void reset(UUID id) {
        ConfigurationSection s = data.getConfigurationSection("players." + id);
        if (s == null) return;
        data.set("players." + id + ".jour", null);
        data.set("players." + id + ".semaine", null);
        dirty = true;
    }

    void saveIfDirty() {
        if (!dirty) return;
        try {
            data.save(file);
            dirty = false;
        } catch (IOException e) {
            plugin.getLogger().warning("Quêtes non sauvegardées : " + e.getMessage());
        }
    }
}
