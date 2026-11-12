package fr.citadelle.messages;

import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.command.TabExecutor;
import org.bukkit.entity.Player;

import java.util.List;
import java.util.Locale;

/** /maisons [place | retirer | reset | reload] */
final class HousesCommand implements TabExecutor {

    private static final String ADMIN = "citadelle.maisons.admin";
    private static final String P = "§6⚜ §7";
    private static final int CHAT_TOP = 10;

    private final CitadelleMessages plugin;
    private final HousesBoard board;

    HousesCommand(CitadelleMessages plugin, HousesBoard board) {
        this.plugin = plugin;
        this.board = board;
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (args.length == 0) {
            sender.sendMessage("");
            sender.sendMessage("§6§l   ⚜ LES GRANDES MAISONS ⚜");
            for (String line : board.lines(CHAT_TOP)) sender.sendMessage("   " + line);
            sender.sendMessage("   " + board.formula());
            sender.sendMessage("");
            return true;
        }
        if (!sender.hasPermission(ADMIN)) {
            sender.sendMessage(P + "Tu n'as pas la permission.");
            return true;
        }
        switch (args[0].toLowerCase(Locale.ROOT)) {
            case "place" -> {
                if (sender instanceof Player p) {
                    board.place(p.getLocation());
                    sender.sendMessage(P + "Le classement est installé ici, tourné vers toi.");
                } else sender.sendMessage(P + "Place-toi à l'endroit voulu en jeu.");
            }
            case "retirer" -> { board.removeForGood(); sender.sendMessage(P + "Classement retiré."); }
            case "reset" -> { board.resetWins(); sender.sendMessage(P + "Victoires de faille remises à zéro."); }
            case "reload" -> { plugin.reloadConfig(); board.respawn(); sender.sendMessage(P + "Classement rechargé."); }
            default -> sender.sendMessage(P + "/maisons [place | retirer | reset | reload]");
        }
        return true;
    }

    @Override
    public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        if (!sender.hasPermission(ADMIN) || args.length != 1) return List.of();
        return List.of("place", "retirer", "reset", "reload").stream().filter(s -> s.startsWith(args[0].toLowerCase(Locale.ROOT))).toList();
    }
}
