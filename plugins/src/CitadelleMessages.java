package fr.citadelle.messages;

import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.OfflinePlayer;
import org.bukkit.entity.Player;
import org.bukkit.event.Event;
import org.bukkit.event.EventPriority;
import org.bukkit.event.Listener;
import org.bukkit.plugin.Plugin;
import org.bukkit.plugin.java.JavaPlugin;

import java.lang.reflect.Method;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * La Citadelle - "Régénération" death/respawn effects (see Regeneration) and styled fake join/quit messages when staff vanish / unvanish with Staff++
 * (works for /v and for staff mode). Uses PlaceholderAPI for the LuckPerms prefix and
 * translates '&' colour codes (and &#RRGGBB hex) before broadcasting.
 */
public final class CitadelleMessages extends JavaPlugin implements Listener {

    private static final Pattern HEX = Pattern.compile("&#([0-9a-fA-F]{6})");
    private Method papiSet;
    private TimeRift rift;

    @Override
    public void onDisable() {
        if (rift != null) rift.shutdown();
    }

    @Override
    public void onEnable() {
        saveDefaultConfig();
        getServer().getPluginManager().registerEvents(new Regeneration(this), this);
        rift = new TimeRift(this);
        org.bukkit.command.PluginCommand faille = getCommand("faille");
        if (faille != null) {
            RiftCommand cmd = new RiftCommand(this, rift);
            faille.setExecutor(cmd);
            faille.setTabCompleter(cmd);
        }
        Plugin papi = Bukkit.getPluginManager().getPlugin("PlaceholderAPI");
        if (papi != null) {
            try {
                Class<?> c = Class.forName("me.clip.placeholderapi.PlaceholderAPI", true, papi.getClass().getClassLoader());
                papiSet = c.getMethod("setPlaceholders", OfflinePlayer.class, String.class);
            } catch (Exception e) {
                getLogger().warning("PlaceholderAPI introuvable : " + e);
            }
        }
        Plugin staff = Bukkit.getPluginManager().getPlugin("StaffPlusPlus");
        if (staff == null) {
            getLogger().warning("Staff++ absent : aucun message de vanish.");
            return;
        }
        ClassLoader cl = staff.getClass().getClassLoader();
        hook(cl, "net.shortninja.staffplusplus.vanish.VanishOnEvent", true);
        hook(cl, "net.shortninja.staffplusplus.vanish.VanishOffEvent", false);
    }

    @SuppressWarnings("unchecked")
    private void hook(ClassLoader cl, String name, boolean vanishOn) {
        try {
            Class<? extends Event> type = (Class<? extends Event>) Class.forName(name, true, cl);
            getServer().getPluginManager().registerEvent(type, this, EventPriority.MONITOR,
                    (listener, event) -> {
                        if (type.isInstance(event)) handle(event, vanishOn);
                    }, this, true);
            getLogger().info("Ecoute de " + type.getSimpleName());
        } catch (Exception e) {
            getLogger().warning("Impossible d'ecouter " + name + " : " + e);
        }
    }

    private void handle(Event event, boolean vanishOn) {
        try {
            Player player = (Player) event.getClass().getMethod("getPlayer").invoke(event);
            if (player == null) return;
            if (vanishOn && isOnJoin(event)) return;            // logged in already vanished: stay silent
            String type = String.valueOf(invokeOrNull(event, "getType"));
            if ("NONE".equalsIgnoreCase(type)) return;
            String template = getConfig().getString(vanishOn ? "fake-quit" : "fake-join", "");
            if (template == null || template.isEmpty()) return;
            String msg = template.replace("{player}", player.getName());
            msg = papi(player, msg);
            final String out = colour(msg);
            Bukkit.getScheduler().runTask(this, () -> Bukkit.broadcastMessage(out));
        } catch (Exception e) {
            getLogger().warning("Erreur message de vanish : " + e);
        }
    }

    private boolean isOnJoin(Event event) {
        for (String m : new String[]{"isOnJoin", "getOnJoin", "onJoin"}) {
            Object v = invokeOrNull(event, m);
            if (v instanceof Boolean) return (Boolean) v;
        }
        return false;
    }

    private Object invokeOrNull(Object o, String method) {
        try {
            Method m = o.getClass().getMethod(method);
            return m.invoke(o);
        } catch (Exception ignored) {
            return null;
        }
    }

    private String papi(Player p, String s) {
        if (papiSet == null) return s;
        try {
            return (String) papiSet.invoke(null, p, s);
        } catch (Exception e) {
            return s;
        }
    }

    static String colour(String s) {
        Matcher m = HEX.matcher(s);
        StringBuffer sb = new StringBuffer();
        while (m.find()) {
            StringBuilder rep = new StringBuilder("§x");
            for (char ch : m.group(1).toCharArray()) rep.append('§').append(ch);
            m.appendReplacement(sb, Matcher.quoteReplacement(rep.toString()));
        }
        m.appendTail(sb);
        return ChatColor.translateAlternateColorCodes('&', sb.toString());
    }
}
