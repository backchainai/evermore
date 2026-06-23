/** Mirrors Pet Data backend Pydantic models. */

export interface Animal {
	id: string;
	name: string;
	aka: string | null;
	breed: string | null;
	weight_lbs: number | null;
	birth_date: string | null;
	intake_date: string | null;
	location: string | null;
	color_category: string | null;
	behavior_mod_tags: string[] | null;
	is_in_kennel: boolean | null;
	is_foster_care: boolean | null;
	photo_url: string | null;
	public_profile_url: string | null;
	age_years: number | null;
	days_in_shelter: number | null;
	is_adoptable: boolean | null;
}

export interface VolunteerNote {
	id: number;
	animal_id: string;
	volunteer_name: string;
	note_date: string;
	note_text: string | null;
	rating_strong_on_leash: number | null;
	rating_leash_reactivity: number | null;
	rating_shy_fearful: number | null;
	rating_jumpy_mouthy: number | null;
}

export interface KennelCard {
	id: number;
	animal_id: string;
	about_text: string | null;
	dogs_compatibility: string | null;
	cats_compatibility: string | null;
	kids_compatibility: string | null;
	commands_known: string | null;
	housebreaking_status: string | null;
	things_likes: string | null;
	things_dislikes: string | null;
}

export interface StaffAssessment {
	id: number;
	animal_id: string;
	assessment_tags: string[] | null;
	notes: string | null;
	recorded_at: string | null;
}

export interface AnimalListResponse {
	animals: Animal[];
	count: number;
}

export interface AnimalDetailResponse {
	animal: Animal;
	kennel_card: KennelCard | null;
	volunteer_notes: VolunteerNote[];
	staff_assessments: StaffAssessment[];
}
