package fr.citadelle.messages;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.Location;
import org.bukkit.entity.Player;
import org.bukkit.plugin.Plugin;

import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.util.logging.Logger;

/**
 * Talks to SaberFactions (FactionsUUID API) through reflection so the plugin compiles without it.
 * Without Factions every player counts as a solo team and no chunk is considered claimed.
 */
final class FactionBridge {

    /** A capturing side: a faction, or a lone player. */
    record Team(String key, String name, boolean solo) { }

    private final Logger log;
    private Object fplayers;
    private Method getByPlayer, getFaction, isWilderness, getTag, getId, getFactionAt;
    private Object board;
    private Constructor<?> flocation;
    private boolean available;

    FactionBridge(Logger log) {
        this.log = log;
        Plugin factions = Bukkit.getPluginManager().getPlugin("Factions");
        if (factions == null) {
            log.warning("Factions absent : la faille comptera chaque joueur seul.");
            return;
        }
        try {
            ClassLoader cl = factions.getClass().getClassLoader();
            Class<?> fpClass = Class.forName("com.massivecraft.factions.FPlayers", true, cl);
            Class<?> fpInterface = Class.forName("com.massivecraft.factions.FPlayer", true, cl);
            Class<?> faction = Class.forName("com.massivecraft.factions.Faction", true, cl);
            Class<?> boardClass = Class.forName("com.massivecraft.factions.Board", true, cl);
            Class<?> flocClass = Class.forName("com.massivecraft.factions.FLocation", true, cl);
            fplayers = fpClass.getMethod("getInstance").invoke(null);
            getByPlayer = fpClass.getMethod("getByPlayer", Player.class);
            getFaction = fpInterface.getMethod("getFaction");
            isWilderness = faction.getMethod("isWilderness");
            getTag = faction.getMethod("getTag");
            getId = faction.getMethod("getId");
            board = boardClass.getMethod("getInstance").invoke(null);
            flocation = flocClass.getConstructor(Location.class);
            getFactionAt = boardClass.getMethod("getFactionAt", flocClass);
            available = true;
        } catch (ReflectiveOperationException | RuntimeException e) {
            log.warning("API Factions inaccessible (" + e + ") : la faille comptera chaque joueur seul.");
        }
    }

    Team teamOf(Player player) {
        if (available) {
            try {
                Object faction = getFaction.invoke(getByPlayer.invoke(fplayers, player));
                if (faction != null && !(Boolean) isWilderness.invoke(faction)) {
                    String tag = ChatColor.stripColor(String.valueOf(getTag.invoke(faction)));
                    return new Team("f:" + getId.invoke(faction), tag, false);
                }
            } catch (ReflectiveOperationException | RuntimeException e) {
                log.fine("Faction de " + player.getName() + " illisible : " + e);
            }
        }
        return new Team("p:" + player.getUniqueId(), player.getName(), true);
    }

    /** true when any chunk within {@code chunkRadius} of loc belongs to a faction (or safezone / warzone). */
    boolean isClaimedAround(Location loc, int chunkRadius) {
        if (!available || loc.getWorld() == null) return false;
        try {
            for (int dx = -chunkRadius; dx <= chunkRadius; dx++) {
                for (int dz = -chunkRadius; dz <= chunkRadius; dz++) {
                    Location probe = loc.clone().add(dx * 16.0, 0, dz * 16.0);
                    Object faction = getFactionAt.invoke(board, flocation.newInstance(probe));
                    if (faction != null && !(Boolean) isWilderness.invoke(faction)) return true;
                }
            }
        } catch (ReflectiveOperationException | RuntimeException e) {
            log.fine("Claims illisibles : " + e);
        }
        return false;
    }
}
