package fr.citadelle.messages;

import org.bukkit.Location;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabExecutor;
import org.bukkit.entity.Player;

import java.util.List;
import java.util.Locale;

/** /faille [info|start [ici]|stop|tp|reload] */
final class RiftCommand implements TabExecutor {

    private static final String ADMIN = "citadelle.faille.admin";
    private static final String P = "§5⌛ §7";

    private final CitadelleMessages plugin;
    private final TimeRift rift;

    RiftCommand(CitadelleMessages plugin, TimeRift rift) {
        this.plugin = plugin;
        this.rift = rift;
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        String sub = args.length == 0 ? "info" : args[0].toLowerCase(Locale.ROOT);
        if (!sub.equals("info") && !sender.hasPermission(ADMIN)) {
            sender.sendMessage(P + "Tu n'as pas la permission.");
            return true;
        }
        switch (sub) {
            case "start" -> {
                Location here = null;
                if (args.length > 1 && args[1].equalsIgnoreCase("ici")) {
                    if (!(sender instanceof Player p)) { sender.sendMessage(P + "« ici » demande d'être en jeu."); return true; }
                    here = p.getLocation();
                }
                String err = rift.start(here);
                sender.sendMessage(err == null ? P + "Faille lancée." : P + "Impossible : " + err + ".");
            }
            case "stop" -> {
                if (rift.phase() == TimeRift.Phase.IDLE) sender.sendMessage(P + "Aucune faille ouverte.");
                else rift.stop(true);
            }
            case "tp" -> {
                Location c = rift.center();
                if (!(sender instanceof Player p)) sender.sendMessage(P + "Commande en jeu uniquement.");
                else if (rift.phase() == TimeRift.Phase.IDLE || c == null) sender.sendMessage(P + "Aucune faille ouverte.");
                else p.teleport(c.add(0, 1, 0));
            }
            case "reload" -> {
                if (rift.phase() != TimeRift.Phase.IDLE) { sender.sendMessage(P + "Attends la fin de la faille pour recharger."); return true; }
                plugin.reloadConfig();
                rift.reload();
                sender.sendMessage(P + "Configuration rechargée.");
            }
            default -> info(sender);
        }
        return true;
    }

    private void info(CommandSender sender) {
        Location c = rift.center();
        switch (rift.phase()) {
            case WARMUP -> sender.sendMessage(P + "Une faille va s'ouvrir en §fX " + c.getBlockX() + " §7/ §fZ " + c.getBlockZ() + "§7.");
            case ACTIVE -> sender.sendMessage(P + "Une faille est ouverte en §fX " + c.getBlockX() + " §7/ §fZ " + c.getBlockZ() + "§7 : fonce !");
            default -> {
                String next = rift.nextTime();
                sender.sendMessage(P + "Aucune faille ouverte." + (next != null ? " Prochaine ouverture prévue à §e" + next + "§7." : ""));
            }
        }
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        if (!sender.hasPermission(ADMIN)) return List.of("info");
        if (args.length == 1) return List.of("info", "start", "stop", "tp", "reload").stream().filter(s -> s.startsWith(args[0].toLowerCase(Locale.ROOT))).toList();
        if (args.length == 2 && args[0].equalsIgnoreCase("start")) return List.of("ici");
        return List.of();
    }
}
