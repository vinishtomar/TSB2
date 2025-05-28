import os
            db.session.commit()
            flash("Entry deleted successfully.", "success")
        else:
            flash("Entry not found.", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting entry: {str(e)}", "danger")
    return redirect(url_for('index'))

@app.route('/modify-history/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def modify_history(entry_id):
    entry = SuiviJournalier.query.get(entry_id)
    if not entry:
        flash("Entrée non trouvée.", "danger")
        return redirect(url_for('index'))
    if current_user.role != "admin" and entry.utilisateur != current_user.id:
        flash("Droits insuffisants pour modifier cette entrée.", "danger")
        return redirect(url_for('index'))
    if request.method == 'POST':
        for field in [
            "equipement_type", "equipement_reference", "equipement_etat", "equipement_date_reception",
            "connecteur_type", "connecteur_quantite", "connecteur_etat",
            "chemin_cable_longueur", "chemin_cable_type",
            "terre_type_raccord", "terre_valeur_resistance",
            "cableac_section", "cableac_longueur",
            "cabledc_section", "cabledc_longueur",
            "cables_dctires", "cables_actires", "cables_terretires",
            "fin_zone", "fin_string", "fin_tension_dc", "fin_courant_dc", "fin_tension_ac", "fin_puissance", "fin_date", "fin_technicien", "fin_status"
        ]:
            setattr(entry, field, request.form.get(field, getattr(entry, field)))
        delete_ids = request.form.getlist('delete_images')
        for img in entry.images[:]:
            if str(img.id) in delete_ids:
                db.session.delete(img)
        photos = request.files.getlist('photo_chantier')
        for photo in photos:
            if photo and photo.filename:
                img = SuiviJournalierImage(
                    suivi_id=entry.id,
                    filename=photo.filename,
                    content_type=photo.content_type,
                    data=photo.read()
                )
                db.session.add(img)
        db.session.commit()
        flash("Entrée modifiée avec succès.", "success")
        return redirect(url_for('index'))
    return render_template('modify_history.html', entry=entry)

def save_to_csv(data):
    filepath = os.path.join('uploads', 'suivi_journalier.csv')
    file_exists = os.path.isfile(filepath)
    fieldnames = [
        "date", "utilisateur",
        "equipement_type", "equipement_reference", "equipement_etat", "equipement_date_reception",
        "connecteur_type", "connecteur_quantite", "connecteur_etat",
        "chemin_cable_longueur", "chemin_cable_type",
        "terre_type_raccord", "terre_valeur_resistance",
        "cableac_section", "cableac_longueur",
        "cabledc_section", "cabledc_longueur",
        "cables_dctires", "cables_actires", "cables_terretires",
        "fin_zone", "fin_string", "fin_tension_dc", "fin_courant_dc", "fin_tension_ac", "fin_puissance", "fin_date", "fin_technicien", "fin_status",
        "photo_chantier"
    ]
    try:
        with open(filepath, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';')
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
    except Exception as e:
        print("❌ CSV save error:", e)

if __name__ == '__main__':
    app.run(debug=True)
