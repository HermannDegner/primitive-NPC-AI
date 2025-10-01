#!/usr/bin/env python3
"""
Subjective Boundary System - 主観的境界システム
SSD理論に基づく「内・外」認知による自然な縄張り形成
物理的土地ではなく、主観集合的認知による境界システム
"""
import random
import math
from collections import defaultdict

class SubjectiveBoundarySystem:
    """主観的境界システム - 内・外認知による自然な共同体形成"""
    
    def __init__(self):
        # 主観的境界マップ {npc_name: {'people': {内の人}, 'places': {内の場所}, 'resources': {内の資源}}}
        self.subjective_boundaries = defaultdict(lambda: {
            'people': set(),
            'places': set(), 
            'resources': set(),
            'activities': set()
        })
        
        # 境界形成の履歴と強度
        self.boundary_strength = defaultdict(lambda: defaultdict(float))  # {npc_name: {object_id: strength}}
        self.boundary_formation_history = defaultdict(list)  # 境界形成の経緯
        
        # 集団的境界（主観集合的認知）
        self.collective_boundaries = defaultdict(set)  # {collective_id: {member_names}}
        self.collective_identity = {}  # {collective_id: {'core_values', 'shared_experiences'}}
        
        # 境界侵犯の記録
        self.boundary_violations = defaultdict(list)
        
        # NPCレジストリの参照（後で設定）
        self.npc_roster = None
        
    def set_npc_roster(self, roster):
        """NPCレジストリの設定"""
        self.npc_roster = roster
        
    def process_subjective_experience(self, npc, experience_type, target_object, context, tick):
        """主観的経験の処理による境界形成"""
        
        # 経験の性質を分析
        experience_valence = self._analyze_experience_valence(npc, experience_type, target_object, context)
        shared_context = self._detect_shared_context(npc, target_object, context, tick)
        
        # 内・外の境界更新
        if experience_valence > 0.3:  # ポジティブな経験
            self._expand_inner_boundary(npc, target_object, experience_type, experience_valence, tick)
        elif experience_valence < -0.3:  # ネガティブな経験
            self._contract_inner_boundary(npc, target_object, experience_type, abs(experience_valence), tick)
        
        # 共有経験による集団的境界形成
        if shared_context['shared_participants']:
            self._form_collective_boundary(npc, shared_context['shared_participants'], 
                                         target_object, experience_type, tick)
        
        # SSD理論：意味圧による境界の動的調整
        self._apply_ssd_boundary_dynamics(npc, experience_valence, shared_context)
    
    def _analyze_experience_valence(self, npc, experience_type, target_object, context):
        """経験の感情価（ポジティブ・ネガティブ）を分析"""
        valence = 0.0
        
        # 経験タイプによる基本価値
        experience_values = {
            'successful_foraging': 0.7,
            'failed_foraging': -0.4,
            'successful_hunting': 0.8,
            'social_cooperation': 0.6,
            'resource_sharing': 0.5,
            'conflict_resolution': 0.3,
            'hostile_encounter': -0.8,
            'resource_theft': -0.9,
            'successful_defense': 0.9,
            'community_building': 0.7,
            'exploration_discovery': 0.4,
            'water_access': 0.6,
            'safe_rest': 0.5,
            'group_hunting': 0.8,
            'territorial_defense': 0.7,
            'friendly_encounter': 0.4
        }
        
        valence += experience_values.get(experience_type, 0.0)
        
        # 個人的特性による修正
        npc_name_lower = npc.name.lower()
        if 'social' in experience_type and any(role in npc_name_lower for role in ['diplomat', 'healer']):
            valence += 0.2
        elif 'defense' in experience_type and any(role in npc_name_lower for role in ['warrior', 'guardian']):
            valence += 0.3
        elif 'discovery' in experience_type and any(role in npc_name_lower for role in ['scholar', 'pioneer']):
            valence += 0.2
        
        # 現在の状態による修正
        if hasattr(npc, 'hunger') and npc.hunger > 150 and 'foraging' in experience_type:
            valence += 0.3  # 空腹時の食料発見はより価値が高い
        
        if hasattr(npc, 'thirst') and npc.thirst > 120 and 'water' in experience_type:
            valence += 0.4  # 渇きでの水発見は極めて重要
        
        return max(-1.0, min(1.0, valence))
    
    def _detect_shared_context(self, npc, target_object, context, tick):
        """共有文脈の検出"""
        shared_context = {
            'shared_participants': [],
            'shared_activities': [],
            'proximity_others': [],
            'collective_significance': 0.0
        }
        
        # 近接する他のNPCを検出
        if self.npc_roster:
            for other_name, other_npc in self.npc_roster.items():
                if other_npc != npc and other_npc.alive:
                    distance = math.sqrt((npc.x - other_npc.x)**2 + (npc.y - other_npc.y)**2)
                    if distance < 15:  # 近接範囲
                        shared_context['proximity_others'].append(other_name)
                        
                        # 同じ活動をしている場合
                        if self._is_similar_activity(npc, other_npc, context):
                            shared_context['shared_participants'].append(other_name)
        
        # 集団的意義の計算
        if shared_context['shared_participants']:
            shared_context['collective_significance'] = min(1.0, len(shared_context['shared_participants']) * 0.3)
        
        return shared_context
    
    def _is_similar_activity(self, npc1, npc2, context):
        """類似活動の判定"""
        # 同じコミュニティメンバーかチェック
        if hasattr(npc1, 'territory') and hasattr(npc2, 'territory'):
            if npc1.territory and npc2.territory and npc1.territory == npc2.territory:
                return True
        
        # 同じ狩りグループかチェック
        if hasattr(npc1, 'hunt_group') and hasattr(npc2, 'hunt_group'):
            if npc1.hunt_group and npc2.hunt_group and npc1.hunt_group == npc2.hunt_group:
                return True
        
        # 両方が探索モードまたは採集モード
        if hasattr(npc1, 'exploration_mode') and hasattr(npc2, 'exploration_mode'):
            return npc1.exploration_mode == npc2.exploration_mode
        
        return False
    
    def _expand_inner_boundary(self, npc, target_object, experience_type, valence, tick):
        """内的境界の拡張（「内」として認識）"""
        object_id = self._get_object_id(target_object, experience_type)
        object_category = self._categorize_object(target_object, experience_type)
        
        # 境界強度の更新
        current_strength = self.boundary_strength[npc.name][object_id]
        new_strength = min(1.0, current_strength + valence * 0.2)
        self.boundary_strength[npc.name][object_id] = new_strength
        
        # カテゴリ別の内的境界に追加
        if new_strength > 0.4:
            if object_category == 'person':
                self.subjective_boundaries[npc.name]['people'].add(object_id)
            elif object_category == 'place':
                self.subjective_boundaries[npc.name]['places'].add(object_id)
            elif object_category == 'resource':
                self.subjective_boundaries[npc.name]['resources'].add(object_id)
            elif object_category == 'activity':
                self.subjective_boundaries[npc.name]['activities'].add(object_id)
        
        # 履歴記録
        self.boundary_formation_history[npc.name].append({
            'tick': tick,
            'action': 'expand_inner',
            'object': object_id,
            'category': object_category,
            'valence': valence,
            'new_strength': new_strength,
            'experience': experience_type
        })
    
    def _contract_inner_boundary(self, npc, target_object, experience_type, negative_valence, tick):
        """内的境界の収縮（「外」として排除）"""
        object_id = self._get_object_id(target_object, experience_type)
        object_category = self._categorize_object(target_object, experience_type)
        
        # 境界強度の減少
        current_strength = self.boundary_strength[npc.name][object_id]
        new_strength = max(-1.0, current_strength - negative_valence * 0.3)
        self.boundary_strength[npc.name][object_id] = new_strength
        
        # 内的境界から除去
        if new_strength < 0.2:
            self.subjective_boundaries[npc.name]['people'].discard(object_id)
            self.subjective_boundaries[npc.name]['places'].discard(object_id)  
            self.subjective_boundaries[npc.name]['resources'].discard(object_id)
            self.subjective_boundaries[npc.name]['activities'].discard(object_id)
        
        # 履歴記録
        self.boundary_formation_history[npc.name].append({
            'tick': tick,
            'action': 'contract_inner',
            'object': object_id,
            'category': object_category,
            'negative_valence': negative_valence,
            'new_strength': new_strength,
            'experience': experience_type
        })
    
    def _form_collective_boundary(self, npc, shared_participants, target_object, experience_type, tick):
        """集団的境界の形成（主観集合的認知）"""
        
        # 参加者グループの識別
        participants = [npc.name] + shared_participants
        participants.sort()  # 一貫した識別のため
        collective_id = f"collective_{'_'.join(participants[:3])}"  # 最初の3人で識別
        
        # 集団メンバーの追加
        self.collective_boundaries[collective_id].update(participants)
        
        # 集団アイデンティティの形成・更新
        if collective_id not in self.collective_identity:
            self.collective_identity[collective_id] = {
                'formation_tick': tick,
                'core_experiences': [],
                'shared_values': set(),
                'boundary_strength': 0.0,
                'internal_cohesion': 0.0
            }
        
        # 共有経験の追加
        collective_info = self.collective_identity[collective_id]
        collective_info['core_experiences'].append({
            'tick': tick,
            'experience_type': experience_type,
            'participants': participants,
            'target_object': str(target_object)
        })
        
        # 結束力の更新
        collective_info['internal_cohesion'] = min(1.0, 
            collective_info['internal_cohesion'] + (len(participants) * 0.1))
        
        # 各メンバーの個人的境界に集団メンバーを「内」として追加
        for participant_name in participants:
            for other_participant in participants:
                if participant_name != other_participant:
                    self.subjective_boundaries[participant_name]['people'].add(other_participant)
                    self.boundary_strength[participant_name][other_participant] = \
                        max(0.6, self.boundary_strength[participant_name].get(other_participant, 0.0) + 0.2)
    
    def _get_object_id(self, target_object, experience_type):
        """対象オブジェクトの一意識別子生成"""
        if isinstance(target_object, str):
            return target_object
        elif hasattr(target_object, 'name'):
            return target_object.name
        elif isinstance(target_object, tuple):  # 位置情報
            return f"location_{target_object[0]}_{target_object[1]}"
        else:
            return f"{experience_type}_object_{hash(str(target_object)) % 10000}"
    
    def _categorize_object(self, target_object, experience_type):
        """対象オブジェクトのカテゴリ分類"""
        if isinstance(target_object, str) and any(role in target_object.lower() 
                                                for role in ['warrior', 'healer', 'scholar', 'leader', 'ssd']):
            return 'person'
        elif hasattr(target_object, 'name') and hasattr(target_object, 'alive'):
            return 'person'
        elif isinstance(target_object, tuple) or 'location' in str(target_object):
            return 'place'
        elif any(resource in experience_type.lower() 
                for resource in ['foraging', 'hunting', 'water', 'berries']):
            return 'resource'
        else:
            return 'activity'
    
    def _apply_ssd_boundary_dynamics(self, npc, experience_valence, shared_context):
        """SSD理論による境界の動的調整"""
        
        # 意味圧による境界調整
        boundary_pressure = abs(experience_valence) * (1.0 + shared_context['collective_significance'])
        
        if boundary_pressure > 0.7:
            # 高い意味圧 → 境界の明確化
            if hasattr(npc, 'E'):
                npc.E = max(0.0, npc.E - (boundary_pressure * 0.1))
            
            # 整合慣性の更新
            if hasattr(npc, 'kappa'):
                if 'boundary_formation' not in npc.kappa:
                    npc.kappa['boundary_formation'] = 0.1
                npc.kappa['boundary_formation'] = min(1.0, npc.kappa['boundary_formation'] + 0.05)
        
        elif boundary_pressure < 0.3:
            # 低い意味圧 → 境界の曖昧化
            if hasattr(npc, 'E'):
                npc.E = min(2.0, npc.E + 0.05)
    
    def check_boundary_interaction(self, actor, target, interaction_type, context, tick):
        """境界相互作用のチェック"""
        
        target_id = self._get_object_id(target, interaction_type)
        is_internal = self._is_within_boundary(actor, target_id, interaction_type)
        
        # 境界侵犯の検出
        if not is_internal and interaction_type in ['resource_use', 'territory_enter', 'social_approach']:
            violation = self._detect_boundary_violation(actor, target, interaction_type, context, tick)
            if violation:
                return self._handle_boundary_violation(violation, tick)
        
        # 内部相互作用の場合
        elif is_internal:
            return self._handle_internal_interaction(actor, target, interaction_type, context, tick)
        
        return {'allowed': True, 'response': 'neutral'}
    
    def _is_within_boundary(self, npc, target_id, interaction_type):
        """対象が境界内（「内」）にあるかの判定"""
        
        # 直接的な境界チェック
        boundaries = self.subjective_boundaries[npc.name]
        
        if target_id in boundaries['people']:
            return True
        elif target_id in boundaries['places']:
            return True
        elif target_id in boundaries['resources']:
            return True
        elif target_id in boundaries['activities']:
            return True
        
        # 集団的境界チェック
        for collective_id, members in self.collective_boundaries.items():
            if npc.name in members and target_id in members:
                return True
        
        # 境界強度による判定
        strength = self.boundary_strength[npc.name].get(target_id, 0.0)
        return strength > 0.3
    
    def _detect_boundary_violation(self, actor, target, interaction_type, context, tick):
        """境界侵犯の検出"""
        
        # 対象の所有者/保護者を特定
        protectors = []
        target_id = self._get_object_id(target, interaction_type)
        
        if self.npc_roster:
            for npc_name, npc in self.npc_roster.items():
                if npc_name != actor.name and npc.alive:
                    boundaries = self.subjective_boundaries[npc_name]
                    if (target_id in boundaries['people'] or 
                        target_id in boundaries['places'] or 
                        target_id in boundaries['resources']):
                        
                        # 境界強度をチェック
                        strength = self.boundary_strength[npc_name].get(target_id, 0.0)
                        if strength > 0.4:
                            # 距離チェック（近くにいる場合のみ反応）
                            distance = math.sqrt((actor.x - npc.x)**2 + (actor.y - npc.y)**2)
                            if distance < 20:
                                protectors.append((npc_name, strength))
        
        if protectors:
            # 最も強い主張者を選択
            primary_protector, strength = max(protectors, key=lambda x: x[1])
            
            return {
                'violator': actor.name,
                'target': target_id,
                'protector': primary_protector,
                'protection_strength': strength,
                'interaction_type': interaction_type,
                'context': context,
                'supporting_protectors': [p[0] for p in protectors if p[0] != primary_protector]
            }
        
        return None
    
    def _handle_boundary_violation(self, violation, tick):
        """境界侵犯の処理"""
        
        if not self.npc_roster:
            return {'allowed': True, 'response': 'neutral'}
            
        protector_npc = self.npc_roster.get(violation['protector'])
        violator_npc = self.npc_roster.get(violation['violator'])
        
        if not protector_npc or not violator_npc:
            return {'allowed': True, 'response': 'neutral'}
        
        # 保護反応の決定
        protection_intensity = violation['protection_strength']
        group_support = len(violation['supporting_protectors'])
        
        if protection_intensity > 0.8 or group_support > 2:
            # 強い保護反応
            response = self._generate_strong_protection_response(violation, tick)
        elif protection_intensity > 0.5:
            # 中程度の保護反応
            response = self._generate_moderate_protection_response(violation, tick)
        else:
            # 軽い警告
            response = self._generate_mild_protection_response(violation, tick)
        
        # 違反記録
        self.boundary_violations[violation['target']].append({
            'tick': tick,
            'violator': violation['violator'],
            'protector': violation['protector'],
            'response': response,
            'resolved': response['outcome'] != 'escalation'
        })
        
        return response
    
    def _handle_internal_interaction(self, actor, target, interaction_type, context, tick):
        """内部相互作用の処理（共有・協力）"""
        
        # 内部での協力的相互作用
        cooperation_bonus = 0.2
        
        # 共有経験として記録
        self.process_subjective_experience(
            actor, f"internal_{interaction_type}", target, context, tick
        )
        
        return {
            'allowed': True,
            'response': 'cooperative',
            'cooperation_bonus': cooperation_bonus,
            'message': f"{actor.name} shares resources with inner circle member"
        }
    
    def _generate_strong_protection_response(self, violation, tick):
        """強い保護反応の生成"""
        
        return {
            'allowed': False,
            'response': 'aggressive_defense',
            'message': f"{violation['protector']} and allies aggressively defend against {violation['violator']}",
            'outcome': 'forced_retreat',
            'group_action': True,
            'supporters': violation['supporting_protectors']
        }
    
    def _generate_moderate_protection_response(self, violation, tick):
        """中程度の保護反応の生成"""
        
        return {
            'allowed': False,
            'response': 'firm_warning',
            'message': f"{violation['protector']} firmly warns {violation['violator']} away from protected area",
            'outcome': 'negotiation_possible',
            'group_action': len(violation['supporting_protectors']) > 0
        }
    
    def _generate_mild_protection_response(self, violation, tick):
        """軽い保護反応の生成"""
        
        return {
            'allowed': True,
            'response': 'mild_concern',
            'message': f"{violation['protector']} expresses concern about {violation['violator']}'s actions",
            'outcome': 'monitoring',
            'group_action': False
        }
    
    def get_boundary_analysis(self, roster):
        """境界システムの分析"""
        
        analysis = {
            'individual_boundaries': {},
            'collective_boundaries': {},
            'boundary_violations': 0,
            'internal_cohesion': {},
            'external_conflicts': 0
        }
        
        # 個人境界分析
        for npc_name, boundaries in self.subjective_boundaries.items():
            if npc_name in roster and roster[npc_name].alive:
                analysis['individual_boundaries'][npc_name] = {
                    'inner_people': len(boundaries['people']),
                    'inner_places': len(boundaries['places']),
                    'inner_resources': len(boundaries['resources']),
                    'inner_activities': len(boundaries['activities']),
                    'boundary_clarity': self._calculate_boundary_clarity(npc_name)
                }
        
        # 集団境界分析
        for collective_id, members in self.collective_boundaries.items():
            alive_members = [m for m in members if m in roster and roster[m].alive]
            if len(alive_members) > 1:
                collective_info = self.collective_identity.get(collective_id, {})
                analysis['collective_boundaries'][collective_id] = {
                    'members': alive_members,
                    'cohesion': collective_info.get('internal_cohesion', 0.0),
                    'shared_experiences': len(collective_info.get('core_experiences', []))
                }
        
        # 違反統計
        analysis['boundary_violations'] = sum(len(violations) for violations in self.boundary_violations.values())
        
        return analysis
    
    def _calculate_boundary_clarity(self, npc_name):
        """境界の明確性計算"""
        strengths = list(self.boundary_strength[npc_name].values())
        if not strengths:
            return 0.0
        
        # 明確な境界（強度0.5以上）の割合
        clear_boundaries = [s for s in strengths if abs(s) > 0.5]
        return len(clear_boundaries) / len(strengths) if strengths else 0.0


# SSDシステムへの統合関数
def integrate_subjective_boundary_system():
    """主観的境界システムをSSDに統合"""
    
    global boundary_system
    boundary_system = SubjectiveBoundarySystem()
    
    def process_npc_experience_with_boundaries(npc, action_result, context, tick):
        """境界システム統合版のNPC経験処理"""
        
        # 経験タイプの判定
        experience_type = 'neutral_experience'
        
        if action_result.get('success'):
            if context.get('action') == 'foraging':
                experience_type = 'successful_foraging'
            elif context.get('action') == 'hunting':
                experience_type = 'successful_hunting'
            elif context.get('action') == 'water':
                experience_type = 'water_access'
            elif context.get('social_interaction'):
                experience_type = 'social_cooperation'
            elif context.get('action') == 'rest':
                experience_type = 'safe_rest'
        else:
            if context.get('action') == 'foraging':
                experience_type = 'failed_foraging'
            elif context.get('conflict'):
                experience_type = 'hostile_encounter'
        
        # 対象オブジェクトの特定
        target_object = context.get('target_location', (npc.x, npc.y))
        if context.get('target_npc'):
            target_object = context['target_npc']
        
        # 主観的経験処理
        boundary_system.process_subjective_experience(
            npc, experience_type, target_object, context, tick
        )
        
        return action_result
    
    def check_interaction_boundaries(actor, target, interaction_type, context, tick):
        """相互作用の境界チェック"""
        return boundary_system.check_boundary_interaction(
            actor, target, interaction_type, context, tick
        )
    
    return process_npc_experience_with_boundaries, check_interaction_boundaries


# グローバル変数
boundary_system = None