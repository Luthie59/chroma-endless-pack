package fr.citadelle.messages;

import org.bukkit.Bukkit;
import org.bukkit.OfflinePlayer;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabExecutor;
import org.bukkit.entity.Player;

import java.util.List;
import java.util.Locale;

/** /quetes [pnj [retirer] | reset <joueur> | reload] */
final class QuestCommand implements TabExecutor {

    private static final String ADMIN = "citadelle.quetes.admin";
    private static final String P = "§6✎ §7";

    private final CitadelleMessages plugin;
    private final QuestBook book;
    private final QuestMenu menu;
    private final CitadelleNpc npc;

    QuestCommand(CitadelleMessages plugin, QuestBook book, QuestMenu menu, CitadelleNpc npc) {
        this.plugin = plugin;
        this.book = book;
        this.menu = menu;
        this.npc = npc;
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (args.length == 0) {
            if (sender instanceof Player p) menu.open(p);
            else sender.sendMessage(P + "Commande en jeu uniquement.");
            return true;
        }
        if (!sender.hasPermission(ADMIN)) {
            sender.sendMessage(P + "Tu n'as pas la permission.");
            return true;
        }
        switch (args[0].toLowerCase(Locale.ROOT)) {
            case "pnj" -> {
                if (args.length > 1 && args[1].equalsIgnoreCase("retirer")) {
                    npc.removeForGood();
                    sender.sendMessage(P + "L'Archiviste a été retiré.");
                } else if (sender instanceof Player p) {
                    npc.place(p.getLocation());
                    sender.sendMessage(P + "L'Archiviste est installé ici.");
                } else sender.sendMessage(P + "Place-toi à l'endroit voulu en jeu.");
            }
            case "reset" -> {
                if (args.length < 2) { sender.sendMessage(P + "/quetes reset <joueur>"); return true; }
                @SuppressWarnings("deprecation")
                OfflinePlayer target = Bukkit.getOfflinePlayer(args[1]);
                book.store().reset(target.getUniqueId());
                book.save();
                sender.sendMessage(P + "Quêtes du jour et de la semaine remises à zéro pour " + args[1] + ".");
            }
            case "reload" -> {
                plugin.reloadConfig();
                book.load();
                npc.respawn();
                sender.sendMessage(P + "Quêtes de l'Archiviste rechargées.");
            }
            default -> sender.sendMessage(P + "/quetes [pnj [retirer] | reset <joueur> | reload]");
        }
        return true;
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        if (!sender.hasPermission(ADMIN)) return List.of();
        if (args.length == 1) return List.of("pnj", "reset", "reload").stream().filter(s -> s.startsWith(args[0].toLowerCase(Locale.ROOT))).toList();
        if (args.length == 2 && args[0].equalsIgnoreCase("pnj")) return List.of("retirer");
        if (args.length == 2 && args[0].equalsIgnoreCase("reset")) return null;
        return List.of();
    }
}
