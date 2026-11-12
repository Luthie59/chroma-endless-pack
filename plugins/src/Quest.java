package fr.citadelle.messages;

import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.Tag;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.entity.Enemy;
import org.bukkit.entity.Entity;

import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.logging.Logger;

/** One Archiviste quest definition (from config "archiviste.quetes.<id>"). */
record Quest(String id, Period period, Type type, Set<String> targets, int amount, String name, String objective,
             Material icon, int chronons, int money, List<String> commands) {

    enum Period { JOUR, SEMAINE }

    enum Type { TUER, TUER_JOUEUR, MINER, RECOLTER, PECHER, FAILLE_PARTICIPER, FAILLE_GAGNER }

    static Quest parse(String id, ConfigurationSection s, Logger log) {
        try {
            Period period = Period.valueOf(s.getString("periode", "jour").toUpperCase(Locale.ROOT));
            Type type = Type.valueOf(s.getString("type", "TUER").toUpperCase(Locale.ROOT));
            Set<String> targets = new HashSet<>();
            for (String t : s.getStringList("cibles")) targets.add(t.trim().toUpperCase(Locale.ROOT));
            Material icon = Material.matchMaterial(s.getString("icone", "PAPER"));
            return new Quest(id, period, type, Set.copyOf(targets), Math.max(1, s.getInt("nombre", 1)),
                    CitadelleMessages.colour(s.getString("nom", id)), CitadelleMessages.colour(s.getString("objectif", "")),
                    icon == null ? Material.PAPER : icon, Math.max(0, s.getInt("chronons", 0)), Math.max(0, s.getInt("argent", 0)),
                    s.getStringList("commandes"));
        } catch (IllegalArgumentException e) {
            log.warning("Quête invalide « " + id + " » : " + e.getMessage());
            return null;
        }
    }

    /** kill quests: entity type name, HOSTILE (any monster) or ANY. */
    boolean matchesEntity(Entity e) {
        if (targets.isEmpty() || targets.contains("ANY")) return true;
        if (targets.contains("HOSTILE") && e instanceof Enemy) return true;
        return targets.contains(e.getType().name());
    }

    /** block quests: material name, "#tag" (minecraft block tag, e.g. #LOGS) or ANY. */
    boolean matchesBlock(Material m) {
        if (targets.isEmpty() || targets.contains("ANY")) return true;
        if (targets.contains(m.name())) return true;
        for (String t : targets) {
            if (!t.startsWith("#")) continue;
            Tag<Material> tag = Bukkit.getTag(Tag.REGISTRY_BLOCKS, NamespacedKey.minecraft(t.substring(1).toLowerCase(Locale.ROOT)), Material.class);
            if (tag != null && tag.isTagged(m)) return true;
        }
        return false;
    }
}
