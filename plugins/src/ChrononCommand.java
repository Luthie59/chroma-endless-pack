package fr.citadelle.messages;

import org.bukkit.Bukkit;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabExecutor;
import org.bukkit.entity.Player;

import java.util.List;
import java.util.Locale;

/** /chronon [pnj [retirer] | donner <joueur> <n> | reload] */
final class ChrononCommand implements TabExecutor {

    private static final String ADMIN = "citadelle.chronon.admin";
    private static final String P = "§5⌛ §7";

    private final CitadelleMessages plugin;
    private final Chronon chronon;
    private final ChrononShop shop;
    private final Horloger horloger;

    ChrononCommand(CitadelleMessages plugin, Chronon chronon, ChrononShop shop, Horloger horloger) {
        this.plugin = plugin;
        this.chronon = chronon;
        this.shop = shop;
        this.horloger = horloger;
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (args.length == 0) {
            if (sender instanceof Player p) shop.open(p);
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
                    horloger.removeForGood();
                    sender.sendMessage(P + "L'Horloger a été retiré.");
                } else if (sender instanceof Player p) {
                    horloger.place(p.getLocation());
                    sender.sendMessage(P + "L'Horloger est installé ici.");
                } else {
                    sender.sendMessage(P + "Place-toi à l'endroit voulu en jeu.");
                }
            }
            case "donner" -> give(sender, args);
            case "reload" -> {
                plugin.reloadConfig();
                shop.load();
                horloger.respawn();
                sender.sendMessage(P + "Offres de l'Horloger rechargées.");
            }
            default -> sender.sendMessage(P + "/chronon [pnj [retirer] | donner <joueur> <n> | reload]");
        }
        return true;
    }

    private void give(CommandSender sender, String[] args) {
        if (args.length < 3) { sender.sendMessage(P + "/chronon donner <joueur> <nombre>"); return; }
        Player target = Bukkit.getPlayerExact(args[1]);
        if (target == null) { sender.sendMessage(P + "Joueur introuvable."); return; }
        int n;
        try {
            n = Integer.parseInt(args[2]);
        } catch (NumberFormatException e) {
            sender.sendMessage(P + "Nombre invalide.");
            return;
        }
        if (n < 1 || n > 6400) { sender.sendMessage(P + "Entre 1 et 6400."); return; }
        for (int left = n; left > 0; left -= 64) {
            target.getInventory().addItem(chronon.fragment(Math.min(64, left)))
                    .values().forEach(it -> target.getWorld().dropItemNaturally(target.getLocation(), it));
        }
        sender.sendMessage(P + n + " fragments donnés à " + target.getName() + ".");
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        if (!sender.hasPermission(ADMIN)) return List.of();
        if (args.length == 1) return List.of("pnj", "donner", "reload").stream().filter(s -> s.startsWith(args[0].toLowerCase(Locale.ROOT))).toList();
        if (args.length == 2 && args[0].equalsIgnoreCase("pnj")) return List.of("retirer");
        if (args.length == 2 && args[0].equalsIgnoreCase("donner")) return null;   // player names
        return List.of();
    }
}
