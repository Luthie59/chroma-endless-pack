package fr.citadelle.messages;

import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.attribute.Attribute;
import org.bukkit.attribute.AttributeInstance;
import org.bukkit.entity.Entity;
import org.bukkit.entity.LivingEntity;
import org.bukkit.entity.Mob;
import org.bukkit.entity.Stray;
import org.bukkit.entity.Vindicator;
import org.bukkit.entity.WitherSkeleton;
import org.bukkit.entity.Zombie;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.entity.EntityCombustEvent;
import org.bukkit.event.entity.EntityDeathEvent;
import org.bukkit.inventory.EntityEquipment;
import org.bukkit.inventory.ItemStack;

import java.util.HashSet;
import java.util.Random;
import java.util.Set;
import java.util.UUID;

/** "Échos temporels": the creatures that pour out of the rift, their guardian and the chronon fragments. */
final class RiftMobs implements Listener {

    static final String MOB_TAG = "citadelle_faille_mob";
    private static final double FRAGMENT_CHANCE = 0.45;
    private static final double GUARDIAN_RELIC_CHANCE = 0.30;
    private static final double SPAWN_MIN = 5, SPAWN_MAX = 13;

    private final Chronon chronon;
    private final Random rnd = new Random();
    private final Set<UUID> alive = new HashSet<>();
    private UUID guardian;

    RiftMobs(Chronon chronon) {
        this.chronon = chronon;
    }

    ItemStack fragment(int amount) {
        return chronon.fragment(amount);
    }

    int aliveCount() {
        alive.removeIf(id -> {
            Entity e = org.bukkit.Bukkit.getEntity(id);
            return e == null || !e.isValid() || e.isDead();
        });
        return alive.size();
    }

    void spawnWave(Location center, int count) {
        for (int i = 0; i < count; i++) {
            Location at = spot(center);
            if (at == null) continue;
            switch (rnd.nextInt(3)) {
                case 0 -> track(at.getWorld().spawn(at, Zombie.class, z -> {
                    z.setAdult();
                    style(z, "§6Écho du passé", 30, 5);
                    armour(z, Material.GOLDEN_HELMET, Material.IRON_SWORD);
                }));
                case 1 -> track(at.getWorld().spawn(at, Stray.class, s -> {
                    style(s, "§bSentinelle du futur", 26, 4);
                    armour(s, Material.CHAINMAIL_HELMET, Material.BOW);
                }));
                default -> track(at.getWorld().spawn(at, Vindicator.class, v -> {
                    style(v, "§5Ombre temporelle", 28, 6);
                    armour(v, null, Material.IRON_AXE);
                }));
            }
        }
    }

    void spawnGuardian(Location center) {
        Location at = spot(center);
        if (at == null) at = center.clone();
        WitherSkeleton boss = at.getWorld().spawn(at, WitherSkeleton.class, w -> {
            style(w, "§4§l⌛ Gardien de la Faille", 160, 11);
            armour(w, Material.NETHERITE_HELMET, Material.NETHERITE_SWORD);
            w.setGlowing(true);
            setAttr(w, Attribute.KNOCKBACK_RESISTANCE, 0.6);
            setAttr(w, Attribute.MOVEMENT_SPEED, 0.29);
        });
        track(boss);
        guardian = boss.getUniqueId();
    }

    private void track(LivingEntity e) {
        alive.add(e.getUniqueId());
    }

    private static void style(Mob m, String name, double health, double damage) {
        m.addScoreboardTag(MOB_TAG);
        m.setCustomName(name);
        m.setCustomNameVisible(true);
        m.setRemoveWhenFarAway(false);
        m.setPersistent(false);
        m.setCanPickupItems(false);
        setAttr(m, Attribute.MAX_HEALTH, health);
        m.setHealth(health);
        setAttr(m, Attribute.ATTACK_DAMAGE, damage);
    }

    private static void setAttr(LivingEntity e, Attribute a, double value) {
        AttributeInstance inst = e.getAttribute(a);
        if (inst != null) inst.setBaseValue(value);
    }

    private static void armour(LivingEntity e, Material helmet, Material hand) {
        EntityEquipment eq = e.getEquipment();
        if (eq == null) return;
        if (helmet != null) eq.setHelmet(new ItemStack(helmet));
        if (hand != null) eq.setItemInMainHand(new ItemStack(hand));
        eq.setHelmetDropChance(0f);
        eq.setItemInMainHandDropChance(0f);
    }

    private Location spot(Location center) {
        World w = center.getWorld();
        for (int i = 0; i < 8; i++) {
            double a = rnd.nextDouble() * Math.PI * 2, d = SPAWN_MIN + rnd.nextDouble() * (SPAWN_MAX - SPAWN_MIN);
            Location s = RiftLocator.surface(w, center.getBlockX() + (int) (Math.cos(a) * d), center.getBlockZ() + (int) (Math.sin(a) * d));
            if (s != null && Math.abs(s.getY() - center.getY()) < 10) return s;
        }
        return null;
    }

    void clear() {
        for (UUID id : alive) {
            Entity e = org.bukkit.Bukkit.getEntity(id);
            if (e != null) e.remove();
        }
        alive.clear();
        guardian = null;
    }

    @EventHandler
    public void onDeath(EntityDeathEvent event) {
        LivingEntity e = event.getEntity();
        if (!e.getScoreboardTags().contains(MOB_TAG)) return;
        alive.remove(e.getUniqueId());
        event.getDrops().clear();
        if (e.getUniqueId().equals(guardian)) {
            guardian = null;
            event.getDrops().add(fragment(6 + rnd.nextInt(5)));
            event.getDrops().add(new ItemStack(Material.DIAMOND, 3 + rnd.nextInt(4)));
            event.getDrops().add(new ItemStack(Material.NETHERITE_SCRAP, 1));
            if (rnd.nextDouble() < GUARDIAN_RELIC_CHANCE) event.getDrops().add(RiftRelics.randomRelic(rnd));
            event.setDroppedExp(160);
        } else {
            if (rnd.nextDouble() < FRAGMENT_CHANCE) event.getDrops().add(fragment(1));
            event.setDroppedExp(12);
        }
    }

    /** rift creatures don't burn in daylight (plain EntityCombustEvent = sun). */
    @EventHandler(ignoreCancelled = true)
    public void onSunBurn(EntityCombustEvent event) {
        if (event.getClass() == EntityCombustEvent.class && event.getEntity().getScoreboardTags().contains(MOB_TAG)) {
            event.setCancelled(true);
        }
    }
}
